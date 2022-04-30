import io
import logging

import discord

from discord.ext import commands

from classes.embed import Embed, ErrorEmbed
from utils import tools

log = logging.getLogger(__name__)


class ModMailEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or not tools.is_modmail_channel(message.channel):
            return

        permissions = await message.channel.permissions_for(await message.guild.me())
        if permissions.send_messages is False or permissions.embed_links is False:
            return

        prefix = await tools.get_guild_prefix(self.bot, message.guild)
        if message.content.startswith(prefix):
            return

        data = await tools.get_data(self.bot, message.guild.id)
        if data[11] is True:
            return

        if await tools.is_user_banned(self.bot, message.author):
            await message.channel.send(ErrorEmbed("You are banned from this bot."))
            return

        if data[10] is True:
            await self.send_mail_mod(message, prefix, anon=True)
            return

        await self.send_mail_mod(message, prefix)

    async def send_mail_mod(self, message, prefix, anon=False, snippet=False):
        self.bot.prom.tickets_message.inc({})

        data = await tools.get_data(self.bot, message.guild.id)
        user = tools.get_modmail_user(message.channel)

        if user.id in data[9]:
            await message.channel.send(
                ErrorEmbed(
                    "That user is blacklisted from sending a message here. You need to whitelist "
                    "them before you can send them a message."
                )
            )
            return

        try:
            member = await message.guild.fetch_member(user.id)
        except discord.NotFound:
            await message.channel.send(
                ErrorEmbed(
                    f"The user was not found. Use `{prefix}close [reason]` to close this channel."
                )
            )
            return

        if snippet is True:
            message.content = tools.tag_format(message.content, member)

        embed = Embed("Message Received", message.content, colour=0xFF4500, timestamp=True)
        embed.set_author(
            str(message.author) if anon is False else "Anonymous#0000",
            message.author.avatar_url
            if anon is False
            else "https://cdn.discordapp.com/embed/avatars/0.png",
        )
        embed.set_footer(f"{message.guild.name} | {message.guild.id}", message.guild.icon_url)

        files = []
        for file in message.attachments:
            saved_file = io.BytesIO()
            await file.save(saved_file)
            files.append(discord.File(saved_file, file.filename))

        dm_channel = tools.get_modmail_channel(self.bot, message.channel)

        try:
            dm_message = await dm_channel.send(embed, files=files)
        except discord.Forbidden:
            await message.channel.send(
                ErrorEmbed(
                    "The message could not be sent. The user might have disabled Direct Messages."
                )
            )
            return

        embed.title = "Message Sent"
        embed.set_author(
            str(message.author) if anon is False else f"{message.author} (Anonymous)",
            message.author.avatar_url,
        )
        embed.set_footer(f"{member} | {member.id}", member.avatar_url)

        for count, attachment in enumerate(
            [attachment.url for attachment in dm_message.attachments], start=1
        ):
            embed.add_field(f"Attachment {count}", attachment, False)

        for file in files:
            file.reset()

        await message.channel.send(embed, files=files)

        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass


def setup(bot):
    bot.add_cog(ModMailEvents(bot))

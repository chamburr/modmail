import datetime
import io
import logging

import discord

from discord.ext import commands

import config

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

        if await tools.is_user_banned(self.bot, message.author):
            await message.channel.send(
                embed=ErrorEmbed(description="You are banned from this bot.")
            )
            return

        if (await tools.get_data(self.bot, message.guild.id))[10] is True:
            await self.send_mail_mod(message, prefix, anon=True)
            return

        await self.send_mail_mod(message, prefix)

    async def send_mail_mod(self, message, prefix, anon=False, snippet=False):
        self.bot.prom.tickets_message.inc({})

        data = await tools.get_data(self.bot, message.guild.id)
        user = tools.get_modmail_user(message.channel)

        if user.id in data[9]:
            await message.channel.send(
                embed=ErrorEmbed(
                    description="That user is blacklisted from sending a message here. You need to whitelist them "
                    "before you can send them a message."
                )
            )
            return

        member = await message.guild.fetch_member(user.id)
        if not member:
            await message.channel.send(
                embed=ErrorEmbed(
                    description=f"The user was not found. Use `{prefix}close [reason]` to close this channel."
                )
            )
            return

        if snippet is True:
            message.content = tools.tag_format(message.content, member)

        embed = Embed(
            title="Message Received",
            description=message.content,
            colour=config.mod_colour,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_author(
            name=str(message.author) if anon is False else "Anonymous#0000",
            icon_url=message.author.avatar_url
            if anon is False
            else "https://cdn.discordapp.com/embed/avatars/0.png",
        )
        embed.set_footer(
            text=f"{message.guild.name} | {message.guild.id}", icon_url=message.guild.icon_url
        )

        files = []
        for file in message.attachments:
            saved_file = io.BytesIO()
            await file.save(saved_file)
            files.append(discord.File(saved_file, file.filename))

        dm_channel = tools.get_modmail_channel(self.bot, message.channel)

        try:
            dm_message = await dm_channel.send(embed=embed, files=files)
        except discord.Forbidden:
            await message.channel.send(
                embed=ErrorEmbed(
                    description="The message could not be sent. The user might have disabled Direct Messages."
                )
            )
            return

        embed.title = "Message Sent"
        embed.set_author(
            name=str(message.author) if anon is False else f"{message.author} (Anonymous)",
            icon_url=message.author.avatar_url,
        )
        embed.set_footer(text=f"{member} | {member.id}", icon_url=member.avatar_url)

        for count, attachment in enumerate(
            [attachment["url"] for attachment in dm_message.attachments], start=1
        ):
            embed.add_field(name=f"Attachment {count}", value=attachment, inline=False)

        for file in files:
            file.reset()

        await message.channel.send(embed=embed, files=files)

        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass


def setup(bot):
    bot.add_cog(ModMailEvents(bot))

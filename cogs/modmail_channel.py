import datetime
import io
import logging

import discord

from discord.ext import commands

from utils import checks

log = logging.getLogger(__name__)


class ModMailEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or not checks.is_modmail_channel2(self.bot, message.channel):
            return
        if (
            message.channel.permissions_for(message.guild.me).send_messages is False
            or message.channel.permissions_for(message.guild.me).embed_links is False
        ):
            return
        prefix = self.bot.tools.get_guild_prefix(self.bot, message.guild)
        if message.content.startswith(prefix):
            return
        if message.author.id in self.bot.banned_users:
            await message.channel.send(
                embed=discord.Embed(description="You are banned from this bot.", colour=self.bot.error_colour)
            )
            return
        data = await self.bot.get_data(message.guild.id)
        if data[10] is True:
            await self.send_mail_mod(message, prefix, True)
        else:
            await self.send_mail_mod(message, prefix)

    async def send_mail_mod(self, message, prefix, anon: bool = False, msg: str = None, snippet: bool = False):
        self.bot.prom.tickets_message.inc({})
        data = await self.bot.get_data(message.guild.id)
        if self.bot.tools.get_modmail_user(message.channel) in data[9]:
            await message.channel.send(
                embed=discord.Embed(
                    description="That user is blacklisted from sending a message here. You need to whitelist them "
                    "before you can send them a message.",
                    colour=self.bot.error_colour,
                )
            )
            return
        user = self.bot.tools.get_modmail_user(message.channel)
        member = message.guild.get_member(user)
        if member is None:
            try:
                member = await message.guild.fetch_member(user)
            except discord.NotFound:
                await message.channel.send(
                    embed=discord.Embed(
                        description=f"The user was not found. Use `{prefix}close [reason]` to close this channel.",
                        colour=self.bot.error_colour,
                    )
                )
                return
        if snippet is True:
            msg = self.bot.tools.tag_format(msg, member)
        try:
            embed = discord.Embed(
                title="Message Received",
                description=message.content if msg is None else msg,
                colour=self.bot.mod_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_author(
                name=str(message.author) if anon is False else "Anonymous#0000",
                icon_url=message.author.avatar_url
                if anon is False
                else "https://cdn.discordapp.com/embed/avatars/0.png",
            )
            embed.set_footer(text=f"{message.guild.name} | {message.guild.id}", icon_url=message.guild.icon_url)
            files = []
            for file in message.attachments:
                saved_file = io.BytesIO()
                await file.save(saved_file)
                files.append(discord.File(saved_file, file.filename))
            message2 = await member.send(embed=embed, files=files)
            embed.title = "Message Sent"
            embed.set_footer(text=f"{member} | {member.id}", icon_url=member.avatar_url)
            for count, attachment in enumerate([attachment.url for attachment in message2.attachments], start=1):
                embed.add_field(name=f"Attachment {count}", value=attachment, inline=False)
            for file in files:
                file.reset()
            await message.channel.send(embed=embed, files=files)
        except discord.Forbidden:
            await message.channel.send(
                embed=discord.Embed(
                    description="The message could not be sent. The user might have disabled Direct Messages.",
                    colour=self.bot.error_colour,
                )
            )
            return
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass


def setup(bot):
    bot.add_cog(ModMailEvents(bot))

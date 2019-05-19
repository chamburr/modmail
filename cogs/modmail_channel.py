import io
import datetime
import discord
from discord.ext import commands

from utils.tools import get_guild_prefix


class ModMailEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or not message.channel.category_id:
            return
        if message.channel.category_id not in self.bot.all_category or not message.channel.name.isdigit():
            return
        if message.channel.permissions_for(message.guild.me).send_messages is False or \
           message.channel.permissions_for(message.guild.me).embed_links is False:
            return
        prefix = get_guild_prefix(self.bot, message)
        if message.content.startswith(prefix):
            return
        member = message.guild.get_member(int(message.channel.name))
        if member is None:
            return await message.channel.send(
                embed=discord.Embed(
                    title="Member Not Found",
                    description="The user might have left the server. "
                                f"Use `{prefix}close [reason]` to close this channel.",
                    color=self.bot.error_colour,
                )
            )
        try:
            embed = discord.Embed(
                title="Message Received",
                description=message.content,
                color=self.bot.mod_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_author(
                name=f"{message.author.name}#{message.author.discriminator}",
                icon_url=message.author.avatar_url,
            )
            embed.set_footer(text=f"{message.guild.name} | {message.guild.id}", icon_url=message.guild.icon_url)
            files = []
            for file in message.attachments:
                saved_file = io.BytesIO()
                await file.save(saved_file)
                files.append(discord.File(saved_file, file.filename))
            await member.send(embed=embed, files=files)
            embed.title = "Message Sent"
            embed.set_footer(text=f"{member.name}#{member.discriminator} | {member.id}", icon_url=member.avatar_url)
            for file in files:
                file.reset()
            await message.channel.send(embed=embed, files=files)
        except discord.Forbidden:
            return await message.channel.send(
                embed=discord.Embed(
                    title="Failed",
                    description="The message could not be sent. The user might have disabled Direct Messages.",
                    color=self.bot.error_colour,
                )
            )
        try:
            await message.delete()
        except discord.Forbidden:
            pass


def setup(bot):
    bot.add_cog(ModMailEvents(bot))

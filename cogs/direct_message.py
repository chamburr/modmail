import io
import discord
from discord.ext import commands

from utils.tools import get_guild_prefix


class DirectMessageEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return
        prefix = self.bot.config.default_prefix
        if message.content.startswith(prefix):
            return

        def member_in_guild(guild2):
            if guild2.get_member(message.author.id) is not None:
                return True
            else:
                return False

        def channel_in_guild(channel2):
            if channel2.name == str(message.author.id) and channel2.category_id in self.bot.all_category:
                return True
            else:
                return False

        guilds = filter(member_in_guild, self.bot.guilds)
        guild_list = {}
        for guild in guilds:
            try:
                channel = next(filter(channel_in_guild, guild.text_channels))
            except StopIteration:
                channel = None
            if not channel:
                guild_list[guild.id] = False
            else:
                guild_list[guild.id] = True
        if len(guild_list) == 0:
            return await message.channel.send(
                embed=discord.Embed(
                    title="No Server Found",
                    description="None of the servers that you are in has setup ModMail yet. If you expect to see "
                                "something here and you don't know what might have went wrong, please join our "
                                f"support server with the command `{prefix}support`.",
                    color=self.bot.error_colour,
                )
            )
        embeds = []
        current_embed = None
        for guild, existing in guild_list:
            if not current_embed:
                current_embed = discord.Embed(
                    title="Choose Server",
                    description="Select and confirm the server you want this message to be sent to.",
                    color=self.bot.primary_colour,
                )
                current_embed.set_footer(text="Use the reactions to flip pages.")
            current_embed.add_field(
                name=guild,
                value=("Create a new ticket." if existing is False else "")
            )
            if len(current_embed.fields) == 10:
                embeds.append(current_embed)
                current_embed = None



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
            )
            embed.set_author(
                name=f"{message.author.name}#{message.author.discriminator}",
                icon_url=message.author.avatar_url,
            )
            embed.set_footer(text=message.guild.name, icon_url=message.guild.icon_url)
            files = []
            for file in message.attachments:
                saved_file = io.BytesIO()
                await file.save(saved_file)
                files.append(discord.File(saved_file, file.filename))
            await member.send(embed=embed, files=files)
            embed.title = "Message Sent"
            embed.set_footer(text=f"{member.id} | {member.name}#{member.discriminator}", icon_url=member.avatar_url)
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
    bot.add_cog(DirectMessageEvents(bot))

import datetime
import discord
from discord.ext import commands

from utils.tools import get_guild_prefix


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name}#{self.bot.user.discriminator} is online!")
        print('--------')
        await self.bot.wait_until_ready()
        await self.bot.change_presence(
            activity=discord.Game(name=f"DM to Contact Staff | {self.bot.config.default_prefix}help")
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        join_channel = self.bot.get_channel(self.bot.config.join_channel)
        embed = discord.Embed(
            title="Server Join",
            description=f"{guild.name} ({guild.id})",
            color=0x00FF00,
            timestamp=datetime.datetime.now()
        )
        await join_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        c = self.bot.conn.cursor()
        c.execute("DELETE FROM data WHERE guild=?", (guild.id,))
        self.bot.conn.commit()
        join_channel = self.bot.get_channel(self.bot.config.join_channel)
        embed = discord.Embed(
            title="Server Leave",
            description=f"{guild.name} ({guild.id})",
            color=0xFF0000,
            timestamp=datetime.datetime.now()
        )
        await join_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content.startswith(f"<@{self.bot.user.id}>") or message.content.startswith(f"<@!{self.bot.user.id}>"):
            return await message.channel.send(
                embed=discord.Embed(
                    description=f"My prefix in this server is `{get_guild_prefix(self.bot, message)}`. Please use the "
                                f"prefix instead. Run `{get_guild_prefix(self.bot, message)}help` for more information.",
                    color=self.bot.primary_colour,
                )
            )
        if message.guild:
            permissions = message.channel.permissions_for(message.guild.me)
            if permissions.send_messages is False:
                try:
                    return await message.author.send(
                        embed=discord.Embed(
                            description="The permissions `Send Messages` and `Embed Links` are needed for"
                                        "basic commands to work.",
                            color=self.bot.primary_colour,
                        )
                    )
                except discord.Forbidden:
                    pass
            elif permissions.send_messages is True and permissions.embed_links is False:
                return await message.channel.send("The Embed Links permission is needed for basic commands to work.")
        await self.bot.process_commands(message)


def setup(bot):
    bot.add_cog(Events(bot))

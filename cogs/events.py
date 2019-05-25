import asyncio
import datetime
import traceback
import discord
from discord.ext import commands

from utils.tools import get_guild_prefix


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dbl_auth = {"Authorization": bot.config.dbl_token}
        self.stats_updates = bot.loop.create_task(self.stats_updater())

    async def stats_updater(self):
        await self.bot.wait_until_ready()
        while True:
            await self.bot.session.post(
                f"https://discordbots.org/api/bots/{self.bot.user.id}/stats",
                data=self.get_dbl_payload(),
                headers=self.dbl_auth,
            )
            await asyncio.sleep(1800)

    def get_dbl_payload(self):
        return {
            "server_count": len(self.bot.guilds),
            "shard_count": self.bot.shard_count,
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name}#{self.bot.user.discriminator} is online!")
        print('--------')
        await self.bot.wait_until_ready()
        await self.bot.change_presence(
            activity=discord.Game(name=f"DM to Contact Staff | {self.bot.config.default_prefix}help")
        )
        event_channel = self.bot.get_channel(self.bot.config.event_channel)
        await event_channel.send(
            embed=discord.Embed(
                title="Bot Ready",
                color=0x00FF00,
                timestamp=datetime.datetime.utcnow(),
            )
        )

    @commands.Cog.listener()
    async def on_shard_ready(self, shard):
        try:
            event_channel = self.bot.get_channel(self.bot.config.event_channel)
            await event_channel.send(
                embed=discord.Embed(
                    title=f"Shard {shard} Ready",
                    color=0x00FF00,
                    timestamp=datetime.datetime.utcnow(),
                )
            )
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_connect(self):
        try:
            event_channel = self.bot.get_channel(self.bot.config.event_channel)
            await event_channel.send(
                embed=discord.Embed(
                    title=f"Shard Connected",
                    color=0x00FF00,
                    timestamp=datetime.datetime.utcnow(),
                )
            )
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_disconnect(self):
        try:
            event_channel = self.bot.get_channel(self.bot.config.event_channel)
            await event_channel.send(
                embed=discord.Embed(
                    title=f"Shard Disconnected",
                    color=0xFF0000,
                    timestamp=datetime.datetime.utcnow(),
                )
            )
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_resumed(self):
        try:
            event_channel = self.bot.get_channel(self.bot.config.event_channel)
            await event_channel.send(
                embed=discord.Embed(
                    title=f"Shard Resumed",
                    color=self.bot.config.primary_colour,
                    timestamp=datetime.datetime.utcnow(),
                )
            )
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        error_channel = self.bot.get_channel(self.bot.config.error_channel)
        embed = discord.Embed(
            title='Event Error',
            description=f"```py\n{traceback.format_exc()}```",
            color=self.bot.error_colour,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(name='Event', value=event, inline=False)
        args_str = ['```py']
        for index, arg in enumerate(args):
            args_str.append(f'[{index}]: {arg!r}')
        args_str.append('```')
        embed.add_field(name='Args', value='\n'.join(args_str), inline=False)
        await error_channel.send(embed=embed)

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

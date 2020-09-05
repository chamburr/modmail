import asyncio
import datetime
import json
import logging

import discord

from discord.ext import commands

from utils import tools

log = logging.getLogger(__name__)


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.topgg_auth = {"Authorization": bot.config.topgg_token, "Content-Type": "application/json"}
        self.dbots_auth = {"Authorization": bot.config.dbots_token, "Content-Type": "application/json"}
        self.dbl_auth = {"Authorization": bot.config.dbl_token, "Content-Type": "application/json"}
        self.bod_auth = {"Authorization": bot.config.bod_token, "Content-Type": "application/json"}
        self.bfd_auth = {"Authorization": bot.config.bfd_token, "Content-Type": "application/json"}
        self.dboats_auth = {"Authorization": bot.config.dboats_token, "Content-Type": "application/json"}
        if self.bot.config.testing is False and self.bot.cluster == 1:
            self.stats_updates = bot.loop.create_task(self.stats_updater())
        self.bot_stats_updates = bot.loop.create_task(self.bot_stats_updater())
        self.bot_categories_updates = bot.loop.create_task(self.bot_categories_updater())

    async def stats_updater(self):
        while True:
            guilds = await self.bot.cogs["Communication"].handler("guild_count", self.bot.cluster_count)
            if len(guilds) < self.bot.cluster_count:
                await asyncio.sleep(300)
                continue
            guilds = sum(guilds)
            await self.bot.session.post(
                f"https://top.gg/api/bots/{self.bot.user.id}/stats",
                data=json.dumps({"server_count": guilds, "shard_count": self.bot.shard_count}),
                headers=self.topgg_auth,
            )
            await self.bot.session.post(
                f"https://discord.bots.gg/api/v1/bots/{self.bot.user.id}/stats",
                data=json.dumps({"guildCount": guilds, "shardCount": self.bot.shard_count}),
                headers=self.dbots_auth,
            )
            await self.bot.session.post(
                f"https://discordbotlist.com/api/v1/bots/{self.bot.user.id}/stats",
                data=json.dumps({"guilds": guilds}),
                headers=self.dbl_auth,
            )
            await self.bot.session.post(
                f"https://bots.ondiscord.xyz/bot-api/bots/{self.bot.user.id}/guilds",
                data=json.dumps({"guildCount": guilds}),
                headers=self.bod_auth,
            )
            await self.bot.session.post(
                f"https://botsfordiscord.com/api/bot/{self.bot.user.id}",
                data=json.dumps({"server_count": guilds}),
                headers=self.bfd_auth,
            )
            await self.bot.session.post(
                f"https://discord.boats/api/v2/bot/{self.bot.user.id}",
                data=json.dumps({"server_count": guilds}),
                headers=self.dboats_auth,
            )
            await asyncio.sleep(900)

    async def bot_stats_updater(self):
        while True:
            async with self.bot.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE stats SET commands=commands+$1, messages=messages+$2, tickets=tickets+$3",
                    self.bot.stats_commands,
                    self.bot.stats_messages,
                    self.bot.stats_tickets,
                )
                res = await conn.fetch("SELECT identifier, category FROM ban")
                res2 = await conn.fetch("SELECT identfier, expiry FROM premium WHERE expiry IS NOT NULL")
            self.bot.stats_commands = 0
            self.bot.stats_messages = 0
            self.bot.stats_tickets = 0
            self.banned_users = []
            self.banned_guilds = []
            for row in res:
                if row[1] == 0:
                    self.banned_users.append(row[0])
                elif row[1] == 1:
                    self.banned_guilds.append(row[0])
            timestamp = int(datetime.datetime.utcnow().timestamp() * 1000)
            for row in res2:
                if row[1] < timestamp:
                    await tools.wipe_premium(res[0])
            await asyncio.sleep(60)

    async def bot_categories_updater(self):
        while True:
            async with self.bot.pool.acquire() as conn:
                data = await conn.fetch("SELECT category FROM data")
            categories = []
            for row in data:
                categories.append(row[0])
            self.bot.all_category = categories
            await asyncio.sleep(5)

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f"{self.bot.user.name}#{self.bot.user.discriminator} is online!")
        log.info("--------")
        embed = discord.Embed(
            title=f"[Cluster {self.bot.cluster}] Bot Ready",
            colour=0x00FF00,
            timestamp=datetime.datetime.utcnow(),
        )
        await self.bot.http.send_message(self.bot.config.event_channel, None, embed=embed.to_dict())
        await self.bot.change_presence(activity=discord.Game(name=self.bot.config.activity))

    @commands.Cog.listener()
    async def on_shard_ready(self, shard):
        try:
            embed = discord.Embed(
                title=f"[Cluster {self.bot.cluster}] Shard {shard} Ready",
                colour=0x00FF00,
                timestamp=datetime.datetime.utcnow(),
            )
            await self.bot.http.send_message(self.bot.config.event_channel, None, embed=embed.to_dict())
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_shard_connect(self, shard):
        self.bot.prom.events_counter.labels(type="CONNECT").inc()
        try:
            embed = discord.Embed(
                title=f"[Cluster {self.bot.cluster}] Shard {shard} Connected",
                colour=0x00FF00,
                timestamp=datetime.datetime.utcnow(),
            )
            await self.bot.http.send_message(self.bot.config.event_channel, None, embed=embed.to_dict())
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard):
        self.bot.prom.events_counter.labels(type="DISCONNECT").inc()
        try:
            embed = discord.Embed(
                title=f"[Cluster {self.bot.cluster}] Shard {shard} Disconnected",
                colour=0xFF0000,
                timestamp=datetime.datetime.utcnow(),
            )
            await self.bot.http.send_message(self.bot.config.event_channel, None, embed=embed.to_dict())
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_shard_resumed(self, shard):
        self.bot.prom.events_counter.labels(type="RESUME").inc()
        try:
            embed = discord.Embed(
                title=f"[Cluster {self.bot.cluster}] Shard {shard} Resumed",
                colour=self.bot.config.primary_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            await self.bot.http.send_message(self.bot.config.event_channel, None, embed=embed.to_dict())
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.prom.guilds_join_counter.inc()
        embed = discord.Embed(
            title="Server Join",
            description=f"{guild.name} ({guild.id})",
            colour=0x00FF00,
            timestamp=datetime.datetime.utcnow(),
        )
        guilds = sum(await self.bot.cogs["Communication"].handler("guild_count", self.bot.cluster_count))
        embed.set_footer(text=f"{guilds} servers")
        await self.bot.http.send_message(self.bot.config.join_channel, None, embed=embed.to_dict())
        if guild.id in self.bot.banned_guilds:
            await guild.leave()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.bot.prom.guilds_leave_counter.inc()
        async with self.bot.pool.acquire() as conn:
            await conn.execute("DELETE FROM data WHERE guild=$1", guild.id)
        embed = discord.Embed(
            title="Server Leave",
            description=f"{guild.name} ({guild.id})",
            colour=0xFF0000,
            timestamp=datetime.datetime.utcnow(),
        )
        guilds = sum(await self.bot.cogs["Communication"].handler("guild_count", self.bot.cluster_count))
        embed.set_footer(text=f"{guilds} servers")
        await self.bot.http.send_message(self.bot.config.join_channel, None, embed=embed.to_dict())

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        ctx = await self.bot.get_context(message)
        if not ctx.command:
            return
        self.bot.stats_commands += 1
        self.bot.prom.commands_counter.labels(name=ctx.command.name).inc()
        if message.guild:
            if message.guild.id in self.bot.banned_guilds:
                await message.guild.leave()
                return
            permissions = message.channel.permissions_for(message.guild.me)
            if permissions.send_messages is False:
                return
            elif permissions.embed_links is False:
                await message.channel.send("The Embed Links permission is needed for basic commands to work.")
                return
        if message.author.id in self.bot.banned_users:
            await ctx.send(
                embed=discord.Embed(description="You are banned from this bot.", colour=self.bot.error_colour)
            )
            return
        if ctx.command.cog_name in ["Owner", "Admin"] and (
            ctx.author.id in self.bot.config.admins or ctx.author.id in self.bot.config.owners
        ):
            embed = discord.Embed(
                title=ctx.command.name.title(),
                description=ctx.message.content,
                colour=self.bot.primary_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_author(
                name=f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})", icon_url=ctx.author.avatar_url
            )
            await self.bot.http.send_message(self.bot.config.admin_channel, None, embed=embed.to_dict())
        if ctx.prefix == f"<@{self.bot.user.id}> " or ctx.prefix == f"<@!{self.bot.user.id}> ":
            ctx.prefix = self.bot.tools.get_guild_prefix(self.bot, message.guild)
        await self.bot.invoke(ctx)

    @commands.Cog.listener()
    async def on_socket_response(self, message):
        if message.get("op") == 0:
            self.bot.prom.dispatch_counter.labels(type=message.get("t")).inc()


def setup(bot):
    bot.add_cog(Events(bot))

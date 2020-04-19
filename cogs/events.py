import asyncio
import datetime
import json
import logging

import discord

from discord.ext import commands

log = logging.getLogger(__name__)


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dbl_auth = {"Authorization": bot.config.dbl_token, "Content-Type": "application/json"}
        self.dbots_auth = {"Authorization": bot.config.dbots_token, "Content-Type": "application/json"}
        self.bod_auth = {"Authorization": bot.config.bod_token, "Content-Type": "application/json"}
        self.bfd_auth = {"Authorization": bot.config.bfd_token, "Content-Type": "application/json"}
        self.dboats_auth = {"Authorization": bot.config.dboats_token, "Content-Type": "application/json"}
        if self.bot.config.testing is False:
            self.stats_updates = bot.loop.create_task(self.stats_updater())
        self.bot_stats_updates = bot.loop.create_task(self.bot_stats_updater())

    async def stats_updater(self):
        while True:
            guilds = await self.bot.cogs["Communication"].handler("guild_count", self.bot.cluster_count)
            if len(guilds) < self.bot.cluster_count:
                await asyncio.sleep(300)
                continue
            guilds = sum(guilds)
            await self.bot.session.post(
                f"https://top.gg/api/bots/{self.bot.user.id}/stats",
                data=json.dumps(self.get_dbl_payload(guilds)),
                headers=self.dbl_auth,
            )
            await self.bot.session.post(
                f"https://discord.bots.gg/api/v1/bots/{self.bot.user.id}/stats",
                data=json.dumps(self.get_dbots_payload(guilds)),
                headers=self.dbots_auth,
            )
            await self.bot.session.post(
                f"https://bots.ondiscord.xyz/bot-api/bots/{self.bot.user.id}/guilds",
                data=json.dumps(self.get_bod_payload(guilds)),
                headers=self.bod_auth,
            )
            await self.bot.session.post(
                f"https://botsfordiscord.com/api/bot/{self.bot.user.id}",
                data=json.dumps(self.get_bfd_payload(guilds)),
                headers=self.bfd_auth,
            )
            await self.bot.session.post(
                f"https://discord.boats/api/bot/{self.bot.user.id}",
                data=json.dumps(self.get_dboats_payload(guilds)),
                headers=self.dboats_auth,
            )
            await asyncio.sleep(900)

    def get_dbl_payload(self, guilds):
        return {"server_count": guilds, "shard_count": self.bot.shard_count}

    def get_dbots_payload(self, guilds):
        return {"guildCount": guilds, "shardCount": self.bot.shard_count}

    def get_bod_payload(self, guilds):
        return {"guildCount": guilds}

    def get_bfd_payload(self, guilds):
        return {"server_count": guilds}

    def get_dboats_payload(self, guilds):
        return {"server_count": guilds}

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
            await asyncio.sleep(60)

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f"{self.bot.user.name}#{self.bot.user.discriminator} is online!")
        log.info("--------")
        embed = discord.Embed(
            title=f"[Cluster {self.bot.cluster}] Bot Ready", colour=0x00FF00, timestamp=datetime.datetime.utcnow(),
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
    async def on_connect(self):
        try:
            embed = discord.Embed(
                title=f"[Cluster {self.bot.cluster}] Shard Connected",
                colour=0x00FF00,
                timestamp=datetime.datetime.utcnow(),
            )
            await self.bot.http.send_message(self.bot.config.event_channel, None, embed=embed.to_dict())
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_disconnect(self):
        try:
            embed = discord.Embed(
                title=f"[Cluster {self.bot.cluster}] Shard Disconnected",
                colour=0xFF0000,
                timestamp=datetime.datetime.utcnow(),
            )
            await self.bot.http.send_message(self.bot.config.event_channel, None, embed=embed.to_dict())
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_resumed(self):
        try:
            embed = discord.Embed(
                title=f"[Cluster {self.bot.cluster}] Shard Resumed",
                colour=self.bot.config.primary_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            await self.bot.http.send_message(self.bot.config.event_channel, None, embed=embed.to_dict())
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
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


def setup(bot):
    bot.add_cog(Events(bot))

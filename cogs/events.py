import json
import asyncio
import datetime
import logging
import discord
from discord.ext import commands

from utils.tools import get_guild_prefix

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
        self.activity_index = 0
        self.activity_updates = bot.loop.create_task(self.activity_updater())
        self.bot_stats_updates = bot.loop.create_task(self.bot_stats_updater())

    async def stats_updater(self):
        await self.bot.wait_until_ready()
        while True:
            await self.bot.session.post(
                f"https://top.gg/api/bots/{self.bot.user.id}/stats",
                data=json.dumps(self.get_dbl_payload()),
                headers=self.dbl_auth,
            )
            await self.bot.session.post(
                f"https://discord.bots.gg/api/v1/bots/{self.bot.user.id}/stats",
                data=json.dumps(self.get_dbots_payload()),
                headers=self.dbots_auth,
            )
            await self.bot.session.post(
                f"https://bots.ondiscord.xyz/bot-api/bots/{self.bot.user.id}/guilds",
                data=json.dumps(self.get_bod_payload()),
                headers=self.bod_auth,
            )
            await self.bot.session.post(
                f"https://botsfordiscord.com/api/bot/{self.bot.user.id}",
                data=json.dumps(self.get_bfd_payload()),
                headers=self.bfd_auth,
            )
            await self.bot.session.post(
                f"https://discord.boats/api/bot/{self.bot.user.id}",
                data=json.dumps(self.get_dboats_payload()),
                headers=self.dboats_auth,
            )
            await asyncio.sleep(1800)

    def get_dbl_payload(self):
        return {"server_count": len(self.bot.guilds), "shard_count": self.bot.shard_count}

    def get_dbots_payload(self):
        return {"guildCount": len(self.bot.guilds), "shardCount": self.bot.shard_count}

    def get_bod_payload(self):
        return {"guildCount": len(self.bot.guilds)}

    def get_bfd_payload(self):
        return {"server_count": len(self.bot.guilds)}

    def get_dboats_payload(self):
        return {"server_count": len(self.bot.guilds)}

    async def activity_updater(self):
        await self.bot.wait_until_ready()
        while True:
            if self.activity_index + 1 >= len(self.bot.config.activity):
                self.activity_index = 0
            else:
                self.activity_index = self.activity_index + 1
            await self.bot.change_presence(activity=discord.Game(name=self.bot.config.activity[self.activity_index]))
            await asyncio.sleep(12)

    async def bot_stats_updater(self):
        while True:
            c = self.bot.conn.cursor()
            c.execute(
                "UPDATE stats SET commands=?, messages=?, tickets=?",
                (self.bot.total_commands, self.bot.total_messages, self.bot.total_tickets),
            )
            self.bot.conn.commit()
            await asyncio.sleep(12)

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f"{self.bot.user.name}#{self.bot.user.discriminator} is online!")
        log.info("--------")
        await self.bot.wait_until_ready()
        event_channel = self.bot.get_channel(self.bot.config.event_channel)
        await event_channel.send(
            embed=discord.Embed(title="Bot Ready", colour=0x00FF00, timestamp=datetime.datetime.utcnow())
        )

    @commands.Cog.listener()
    async def on_shard_ready(self, shard):
        try:
            event_channel = self.bot.get_channel(self.bot.config.event_channel)
            await event_channel.send(
                embed=discord.Embed(
                    title=f"Shard {shard} Ready", colour=0x00FF00, timestamp=datetime.datetime.utcnow(),
                )
            )
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_connect(self):
        try:
            event_channel = self.bot.get_channel(self.bot.config.event_channel)
            await event_channel.send(
                embed=discord.Embed(title=f"Shard Connected", colour=0x00FF00, timestamp=datetime.datetime.utcnow())
            )
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_disconnect(self):
        try:
            event_channel = self.bot.get_channel(self.bot.config.event_channel)
            await event_channel.send(
                embed=discord.Embed(title=f"Shard Disconnected", colour=0xFF0000, timestamp=datetime.datetime.utcnow())
            )
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_resumed(self):
        try:
            event_channel = self.bot.get_channel(self.bot.config.event_channel)
            await event_channel.send(
                embed=discord.Embed(
                    title=f"Shard Resumed", colour=self.bot.config.primary_colour, timestamp=datetime.datetime.utcnow()
                )
            )
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        join_channel = self.bot.get_channel(self.bot.config.join_channel)
        embed = discord.Embed(
            title="Server Join",
            description=f"{guild.name} ({guild.id})",
            colour=0x00FF00,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=f"{len(self.bot.guilds)} servers")
        await join_channel.send(embed=embed)
        if guild.id in self.bot.banned_guilds:
            return await guild.leave()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        c = self.bot.conn.cursor()
        c.execute("DELETE FROM data WHERE guild=?", (guild.id,))
        self.bot.conn.commit()
        join_channel = self.bot.get_channel(self.bot.config.join_channel)
        embed = discord.Embed(
            title="Server Leave",
            description=f"{guild.name} ({guild.id})",
            colour=0xFF0000,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=f"{len(self.bot.guilds)} servers")
        await join_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        ctx = await self.bot.get_context(message)
        if not ctx.command:
            return
        self.bot.total_commands += 1
        if message.guild:
            if message.guild.id in self.bot.banned_guilds:
                return await message.guild.leave()
            permissions = message.channel.permissions_for(message.guild.me)
            if permissions.send_messages is False:
                return
            elif permissions.embed_links is False:
                return await message.channel.send("The Embed Links permission is needed for basic commands to work.")
        if message.author.id in self.bot.banned_users:
            return await ctx.send(
                embed=discord.Embed(description="You are banned from this bot.", colour=self.bot.error_colour)
            )
        if ctx.command.cog_name in ["Owner", "Admin"] and (
            ctx.author.id in ctx.bot.config.admins or ctx.author.id in ctx.bot.config.owners
        ):
            admin_channel = self.bot.get_channel(self.bot.config.admin_channel)
            embed = discord.Embed(
                title=ctx.command.name.title(),
                description=ctx.message.content,
                colour=self.bot.primary_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_author(
                name=f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})", icon_url=ctx.author.avatar_url
            )
            await admin_channel.send(embed=embed)
        if ctx.prefix == f"<@{self.bot.user.id}> " or ctx.prefix == f"<@!{self.bot.user.id}> ":
            ctx.prefix = get_guild_prefix(self.bot, message)
        await self.bot.invoke(ctx)


def setup(bot):
    bot.add_cog(Events(bot))

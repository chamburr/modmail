import datetime
import logging
import sys
import traceback

import aiohttp
import aioredis
import asyncpg
import config

from discord.ext import commands

from utils import prometheus, tools

log = logging.getLogger(__name__)


class ModMail(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time = datetime.datetime.utcnow()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.cluster = kwargs.get("cluster_id")
        self.cluster_count = kwargs.get("cluster_count")
        self.version = kwargs.get("version")

    @property
    def uptime(self):
        return datetime.datetime.utcnow() - self.start_time

    @property
    def config(self):
        return config

    @property
    def ipc_channel(self):
        return self.config.ipc_channel

    @property
    def tools(self):
        return tools

    @property
    def primary_colour(self):
        return self.config.primary_colour

    @property
    def user_colour(self):
        return self.config.user_colour

    @property
    def mod_colour(self):
        return self.config.mod_colour

    @property
    def error_colour(self):
        return self.config.error_colour

    async def get_data(self, guild):
        async with self.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT * FROM data WHERE guild=$1", guild)
            if not res:
                await conn.execute(
                    "INSERT INTO data VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)",
                    guild,
                    None,
                    None,
                    [],
                    None,
                    None,
                    None,
                    False,
                    [],
                    [],
                    False,
                )
                return await self.get_data(guild)
        return res

    all_prefix = {}
    all_category = []
    banned_guilds = []
    banned_users = []

    async def connect_redis(self):
        self.redis = await aioredis.create_pool("redis://localhost", minsize=5, maxsize=10, loop=self.loop, db=0)
        info = (await self.redis.execute("INFO")).decode()
        for line in info.split("\n"):
            if line.startswith("redis_version"):
                self.redis_version = line.split(":")[1]
                break

    async def connect_postgres(self):
        self.pool = await asyncpg.create_pool(**self.config.database, max_size=50, command_timeout=60)

    async def connect_prometheus(self):
        self.prom = prometheus
        if self.config.testing is False:
            self.prom.start(self)

    async def start_bot(self):
        await self.connect_redis()
        await self.connect_postgres()
        await self.connect_prometheus()
        async with self.pool.acquire() as conn:
            data = await conn.fetch("SELECT guild, prefix, category FROM data")
            bans = await conn.fetch("SELECT identifier, category FROM ban")
        for row in data:
            self.all_prefix[row[0]] = row[1]
            if row[2]:
                self.all_category.append(row[2])
        for row in bans:
            if row[1] == 0:
                self.banned_users.append(row[0])
            elif row[1] == 1:
                self.banned_guilds.append(row[0])
        for extension in self.config.initial_extensions:
            try:
                self.load_extension(extension)
            except Exception:
                log.error(f"Failed to load extension {extension}.", file=sys.stderr)
                log.error(traceback.print_exc())
        await self.start(self.config.token)

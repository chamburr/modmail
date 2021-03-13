import asyncio
import inspect
import logging
import sys
import time
import traceback

import aio_pika
import aiohttp
import aioredis
import asyncpg
import orjson

from discord import utils
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.core import _CaseInsensitiveDict
from discord.ext.commands.view import StringView
from discord.gateway import DiscordWebSocket
from discord.utils import parse_time, to_json

import config

from classes.http import HTTPClient
from classes.misc import Session, Status
from classes.state import State
from utils import tools

log = logging.getLogger(__name__)


def when_mentioned_or(*prefixes):
    def inner(bot):
        r = list(prefixes)
        r = [f"{bot.mention}", f"<@!{bot.id}> "] + r
        return r

    return inner


class ModMail(commands.AutoShardedBot):
    def __init__(self, command_prefix, description=None, **kwargs):
        self.command_prefix = command_prefix
        self.extra_events = {}
        self._BotBase__cogs = {}
        self._BotBase__extensions = {}
        self._checks = []
        self._check_once = []
        self._before_invoke = None
        self._after_invoke = None
        self._help_command = None
        self.description = inspect.cleandoc(description) if description else ""
        self.owner_id = kwargs.get("owner_id")
        self.owner_ids = kwargs.get("owner_ids", set())
        self._skip_check = lambda x, y: x == y
        self.case_insensitive = kwargs.get("case_insensitive", False)
        self.all_commands = _CaseInsensitiveDict() if self.case_insensitive else {}

        self.ws = None
        self.loop = asyncio.get_event_loop()
        self.http = HTTPClient(None, loop=self.loop)

        self._handlers = {"ready": self._handle_ready}
        self._hooks = {}
        self._listeners = {}

        self._closed = False
        self._ready = asyncio.Event()

        self._redis = None
        self._amqp = None
        self._amqp_channel = None
        self._amqp_queue = None

        self.session = aiohttp.ClientSession(loop=self.loop)
        self.http_uri = f"http://{self.config.http_host}:{self.config.http_port}"
        self.cluster = kwargs.get("cluster_id")
        self.cluster_count = kwargs.get("cluster_count")
        self.version = kwargs.get("version")

        self._cogs = [
            "admin",
            "direct_message",
            "configuration",
            "core",
            "error_handler",
            "events",
            "general",
            "miscellaneous",
            "modmail_channel",
            "owner",
            "premium",
            "snippet",
        ]

    @property
    def state(self):
        return self._connection

    @property
    def config(self):
        return config

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

    async def user(self):
        return await self._connection.user()

    async def users(self):
        return await self._connection._users()

    async def guilds(self):
        return await self._connection.guilds()

    async def emojis(self):
        return await self._connection.emojis()

    async def cached_messages(self):
        return await self._connection._messages()

    async def private_channels(self):
        return await self._connection.private_channels()

    async def shard_count(self):
        return int(await self._redis.get("gateway_shards", encoding="utf-8"))

    async def started(self):
        return parse_time(str(await self._connection._get("gateway_started")).split(".")[0])

    async def statuses(self):
        return [Status(x) for x in await self._connection._get("gateway_statuses")]

    async def sessions(self):
        return {int(x): Session(y) for x, y in (await self._connection._get("gateway_sessions")).items()}

    async def get_channel(self, channel_id):
        return await self._connection.get_channel(channel_id)

    async def get_guild(self, guild_id):
        return await self._connection._get_guild(guild_id)

    async def get_user(self, user_id):
        return await self._connection.get_user(user_id)

    async def get_emoji(self, emoji_id):
        pass

    async def get_all_channels(self):
        pass

    async def get_all_members(self):
        pass

    async def _get_state(self, **options):
        return State(
            dispatch=self.dispatch,
            handlers=self._handlers,
            hooks=self._hooks,
            http=self.http,
            loop=self.loop,
            redis=self._redis,
            shard_count=await self.shard_count(),
            **options,
        )

    async def get_context(self, message, *, cls=Context):
        view = StringView(message.content)
        ctx = cls(prefix=None, view=view, bot=self, message=message)

        if self._skip_check(message.author.id, self.id):
            return ctx

        prefix = await self.get_prefix(message)
        invoked_prefix = prefix

        if isinstance(prefix, str):
            if not view.skip_string(prefix):
                return ctx
        else:
            try:
                if message.content.startswith(tuple(prefix)):
                    invoked_prefix = utils.find(view.skip_string, prefix)
                else:
                    return ctx

            except TypeError:
                if not isinstance(prefix, list):
                    raise TypeError(
                        "get_prefix must return either a string or a list of string, "
                        f"not {prefix.__class__.__name__}"
                    )

                for value in prefix:
                    if not isinstance(value, str):
                        raise TypeError(
                            "Iterable command_prefix or list returned from get_prefix must "
                            f"contain only strings, not {value.__class__.__name__}"
                        )

                raise

        invoker = view.get_word()
        ctx.invoked_with = invoker
        ctx.prefix = invoked_prefix
        ctx.command = self.all_commands.get(invoker)
        return ctx

    async def get_data(self, guild):
        async with self.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT * FROM data WHERE guild=$1", guild)
            if not res:
                res = await conn.fetchrow(
                    "INSERT INTO data VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING *",
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
        return res

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        await self.invoke(ctx)

    async def receive_message(self, msg):
        self.ws._dispatch("socket_raw_receive", msg)

        msg = orjson.loads(msg)

        self.ws._dispatch("socket_response", msg)

        op = msg.get("op")
        data = msg.get("d")
        event = msg.get("t")
        old = msg.get("old")

        if op != self.ws.DISPATCH:
            return

        try:
            func = self.ws._discord_parsers[event]
        except KeyError:
            log.debug(f"Unknown event {event}.")
        else:
            try:
                await func(data, old)
            except asyncio.CancelledError:
                pass
            except Exception:
                try:
                    await self.on_error(event)
                except asyncio.CancelledError:
                    pass

        removed = []

        for index, entry in enumerate(self.ws._dispatch_listeners):
            if entry.event != event:
                continue

            future = entry.future
            if future.cancelled():
                removed.append(index)
                continue

            try:
                valid = entry.predicate(data)
            except Exception as exc:
                future.set_exception(exc)
                removed.append(index)
            else:
                if valid:
                    ret = data if entry.result is None else entry.result(data)
                    future.set_result(ret)
                    removed.append(index)

        for index in reversed(removed):
            del self.ws._dispatch_listeners[index]

    async def send_message(self, msg):
        data = to_json(msg)
        self.ws._dispatch("socket_raw_send", data)
        await self._amqp_channel.default_exchange.publish(aio_pika.Message(body=data), routing_key="gateway.send")

    async def create_reaction_menu(self, ctx, pages):
        msg = await ctx.send(embed=pages[0])
        for reaction in ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]:
            await msg.add_reaction(reaction)
        await self.state.sadd(
            "reaction_menus",
            {
                "channel": msg.channel.id,
                "message": msg.id,
                "page": 0,
                "all_pages": [page.to_dict() for page in pages],
                "end": int(time.time()) + 2 * 60,
            },
        )

    all_prefix = {}
    banned_guilds = []
    banned_users = []

    async def connect_amqp(self):
        self._amqp = await aio_pika.connect_robust(self.config.amqp_url)
        self._amqp_channel = await self._amqp.channel()
        self._amqp_queue = await self._amqp_channel.get_queue("gateway.recv")

    async def connect_redis(self):
        self._redis = await aioredis.create_redis_pool(self.config.redis_url, minsize=5, maxsize=10, loop=self.loop)

    async def connect_postgres(self):
        self.pool = await asyncpg.create_pool(self.config.postgres_url, max_size=10, command_timeout=60)

    async def start(self):
        log.info("Starting...")

        await self.connect_amqp()
        await self.connect_redis()
        await self.connect_postgres()

        self._connection = await self._get_state()
        self._connection._get_client = lambda: self

        self.ws = DiscordWebSocket(socket=None, loop=self.loop)
        self.ws.token = self.http.token
        self.ws._connection = self._connection
        self.ws._discord_parsers = self._connection.parsers
        self.ws._dispatch = self.dispatch
        self.ws.call_hooks = self._connection.call_hooks

        await self.http.static_login(self.config.token, bot=True)

        for extension in self._cogs:
            try:
                self.load_extension("cogs." + extension)
            except Exception:
                log.error(f"Failed to load extension {extension}.", file=sys.stderr)
                log.error(traceback.print_exc())

        async with self._amqp_queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process(ignore_processed=True):
                    await self.receive_message(message.body)
                    message.ack()

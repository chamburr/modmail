import asyncio
import logging
import re
import sys
import traceback

import aio_pika
import aiohttp
import aioredis
import asyncpg
import orjson

from discord.ext import commands
from discord.ext.commands.core import _CaseInsensitiveDict
from discord.gateway import DiscordClientWebSocketResponse, DiscordWebSocket
from discord.utils import parse_time

from classes.http import HTTPClient
from classes.misc import Session, Status
from classes.state import State
from utils import tools
from utils.config import Config
from utils.prometheus import Prometheus

log = logging.getLogger(__name__)


class ModMail(commands.AutoShardedBot):
    def __init__(self, command_prefix=None, **kwargs):
        self.command_prefix = command_prefix
        self.extra_events = {}
        self._BotBase__cogs = {}
        self._BotBase__extensions = {}
        self._checks = []
        self._check_once = []
        self._before_invoke = None
        self._after_invoke = None
        self._help_command = None
        self.description = ""
        self.owner_id = None
        self.owner_ids = set()
        self._skip_check = lambda x, y: x == y
        self.case_insensitive = True
        self.all_commands = _CaseInsensitiveDict() if self.case_insensitive else {}
        self.strip_after_prefix = False

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

        self.config = Config()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.http_uri = f"http://{self.config.BOT_API_HOST}:{self.config.BOT_API_PORT}"
        self.id = kwargs.get("bot_id")
        self.cluster = kwargs.get("cluster_id")
        self.cluster_count = kwargs.get("cluster_count")
        self.version = kwargs.get("version")
        self.pool = None
        self.prom = None

        self._enabled_events = [
            "MESSAGE_CREATE",
            "MESSAGE_REACTION_ADD",
            "READY",
        ]

        self._cogs = [
            "admin",
            "configuration",
            "core",
            "direct_message",
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
    def user(self):
        return tools.create_fake_user(self.id)

    async def real_user(self):
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
        return int(await self._connection.get("gateway_shards"))

    async def started(self):
        return parse_time(str(await self._connection.get("gateway_started")).split(".")[0])

    async def statuses(self):
        return [Status(x) for x in await self._connection.get("gateway_statuses")]

    async def sessions(self):
        return {
            int(x): Session(y) for x, y in (await self._connection.get("gateway_sessions")).items()
        }

    async def get_channel(self, channel_id):
        return await self._connection.get_channel(channel_id)

    async def get_guild(self, guild_id):
        return await self._connection._get_guild(guild_id)

    async def get_user(self, user_id):
        return await self._connection.get_user(user_id)

    async def get_emoji(self, emoji_id):
        return await self._connection.get_emoji(emoji_id)

    async def get_all_channels(self):
        pass

    async def get_all_members(self):
        pass

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
            return

        if event not in self._enabled_events:
            return

        try:
            await func(data, old)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event)
            except asyncio.CancelledError:
                pass

    async def send_message(self, msg):
        data = orjson.dumps(msg)
        self.ws._dispatch("socket_raw_send", data)
        await self._amqp_channel.default_exchange.publish(
            aio_pika.Message(body=data), routing_key="gateway.send"
        )

    async def on_http_request_start(self, _session, trace_config_ctx, _params):
        trace_config_ctx.start = asyncio.get_event_loop().time()

    async def on_http_request_end(self, _session, trace_config_ctx, params):
        elapsed = asyncio.get_event_loop().time() - trace_config_ctx.start

        if elapsed > 1:
            log.warning(f"{params.method} {params.url} took {round(elapsed, 2)} seconds")

        route = str(params.url)
        route = re.sub(r"https:\/\/[a-z\.]+\/api\/v[0-9]+", "", route)
        route = re.sub(r"\/[%A-Z0-9]+", "/_id", route)
        route = re.sub(r"\?.+", "", route)

        if not route.startswith("/"):
            return

        self.prom.http.inc(
            {
                "method": params.method,
                "route": route,
                "status": str(params.response.status),
            }
        )

    async def start(self, worker=True):
        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_start.append(self.on_http_request_start)
        trace_config.on_request_end.append(self.on_http_request_end)
        self.http._HTTPClient__session = aiohttp.ClientSession(
            connector=self.http.connector,
            ws_response_class=DiscordClientWebSocketResponse,
            trace_configs=[trace_config],
        )
        self.http._token(self.config.BOT_TOKEN, bot=True)

        self.pool = await asyncpg.create_pool(
            database=self.config.POSTGRES_DATABASE,
            user=self.config.POSTGRES_USERNAME,
            password=self.config.POSTGRES_PASSWORD,
            host=self.config.POSTGRES_HOST,
            port=int(self.config.POSTGRES_PORT),
            max_size=10,
            command_timeout=60,
        )

        self._redis = await aioredis.create_redis_pool(
            (self.config.REDIS_HOST, int(self.config.REDIS_PORT)),
            password=self.config.REDIS_PASSWORD,
            minsize=5,
            maxsize=10,
            loop=self.loop,
        )

        if worker:
            self._amqp = await aio_pika.connect_robust(
                login=self.config.RABBIT_USERNAME,
                password=self.config.RABBIT_PASSWORD,
                host=self.config.RABBIT_HOST,
                port=int(self.config.RABBIT_PORT),
            )
            self._amqp_channel = await self._amqp.channel()
            self._amqp_queue = await self._amqp_channel.get_queue("gateway.recv")

        self.prom = Prometheus(self)
        await self.prom.start()

        self._connection = State(
            id=self.id,
            dispatch=self.dispatch,
            handlers=self._handlers,
            hooks=self._hooks,
            http=self.http,
            loop=self.loop,
            redis=self._redis,
            shard_count=int(await self._redis.get("gateway_shards")),
        )
        self._connection._get_client = lambda: self

        self.ws = DiscordWebSocket(socket=None, loop=self.loop)
        self.ws.token = self.http.token
        self.ws._connection = self._connection
        self.ws._discord_parsers = self._connection.parsers
        self.ws._dispatch = self.dispatch
        self.ws.call_hooks = self._connection.call_hooks

        if not worker:
            return

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
                    await message.ack()

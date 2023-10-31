import asyncio
import copy
import datetime
import inspect
import logging
import os

import orjson

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Deque,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    overload,
)

import discord
from discord import utils
from discord.activity import BaseActivity
from discord.emoji import Emoji
from discord.enums import ChannelType, try_enum, Status
from discord.flags import ApplicationFlags, Intents, MemberCacheFlags
from discord.invite import Invite
from discord.member import VoiceState
from discord.mentions import AllowedMentions
from discord.partial_emoji import PartialEmoji
from discord.sticker import GuildSticker
from discord.raw_models import (
    RawBulkMessageDeleteEvent,
    RawMessageDeleteEvent,
    RawMessageUpdateEvent,
    RawReactionActionEvent,
    RawReactionClearEmojiEvent,
    RawReactionClearEvent,
)
from discord.reaction import Reaction
from discord.role import Role
from discord.user import ClientUser, User
from discord.ui.view import View, ViewStore

from classes.channel import DMChannel, TextChannel, _channel_factory
from classes.guild import Guild
from classes.member import Member
from classes.message import Message


from discord.abc import PrivateChannel
from discord.app_commands import CommandTree, Translator
from discord.gateway import DiscordWebSocket
from classes.guild import GuildChannel
from classes.http import HTTPClient
from classes.message import PartialMessageable as PartialMessageablePayload
from discord.types import gateway as gw
from discord.types.activity import Activity as ActivityPayload
from discord.types.automod import AutoModerationActionExecution, AutoModerationRule
from discord.types.channel import DMChannel as DMChannelPayload
from discord.types.command import (
    GuildApplicationCommandPermissions as GuildApplicationCommandPermissionsPayload,
)
from discord.types.emoji import Emoji as EmojiPayload
from discord.types.emoji import PartialEmoji as PartialEmojiPayload
from discord.types.guild import Guild as GuildPayload
from discord.types.message import Message as MessagePayload
from discord.types.message import PartialMessage as PartialMessagePayload
from discord.types.snowflake import Snowflake
from discord.types.sticker import GuildSticker as GuildStickerPayload
from discord.types.user import PartialUser as PartialUserPayload
from discord.types.user import User as UserPayload
from discord.voice_client import VoiceProtocol

T = TypeVar('T')
Channel = Union[GuildChannel, PrivateChannel, PartialMessagePayload]

_log = logging.getLogger(__name__)

class ChunkRequest:
    def __init__(
        self,
        guild_id: int,
        loop: asyncio.AbstractEventLoop,
        resolver: Callable[[int], Any],
        *,
        cache: bool = True,
    ) -> None:
        self.guild_id: int = guild_id
        self.resolver: Callable[[int], Any] = resolver
        self.loop: asyncio.AbstractEventLoop = loop
        self.cache: bool = cache
        self.nonce: str = os.urandom(16).hex()
        self.buffer: List[Member] = []
        self.waiters: List[asyncio.Future[List[Member]]] = []

    def add_members(self, members: List[Member]) -> None:
        self.buffer.extend(members)
        if self.cache:
            guild = self.resolver(self.guild_id)
            if guild is None:
                return

            for member in members:
                existing = guild.get_member(member.id)
                if existing is None or existing.joined_at is None:
                    guild._add_member(member)

    async def wait(self) -> List[Member]:
        future = self.loop.create_future()
        self.waiters.append(future)
        try:
            return await future
        finally:
            self.waiters.remove(future)

    def get_future(self) -> asyncio.Future[List[Member]]:
        future = self.loop.create_future()
        self.waiters.append(future)
        return future

    def done(self) -> None:
        for future in self.waiters:
            if not future.done():
                future.set_result(self.buffer)


class State:
    def __init__(
        self, *, dispatch, handlers, hooks, http, redis=None, shard_count=None, id, **options
    ):
         # Set later, after Client.login
        self.loop: asyncio.AbstractEventLoop = utils.MISSING
        self.http: HTTPClient = http
        self.max_messages: Optional[int] = options.get('max_messages', 1000)
        if self.max_messages is not None and self.max_messages <= 0:
            self.max_messages = 1000

        self.dispatch: Callable[..., Any] = dispatch
        self.handlers: Dict[str, Callable[..., Any]] = handlers
        self.hooks: Dict[str, Callable[..., Coroutine[Any, Any, Any]]] = hooks
        self.shard_count: Optional[int] = None
        self._ready_task: Optional[asyncio.Task] = None
        self.application_id: Optional[int] = utils._get_as_snowflake(options, 'application_id')
        self.application_flags: ApplicationFlags = utils.MISSING
        self.heartbeat_timeout: float = options.get('heartbeat_timeout', 60.0)
        self.guild_ready_timeout: float = options.get('guild_ready_timeout', 2.0)
        if self.guild_ready_timeout < 0:
            raise ValueError('guild_ready_timeout cannot be negative')

        allowed_mentions = options.get('allowed_mentions')

        if allowed_mentions is not None and not isinstance(allowed_mentions, AllowedMentions):
            raise TypeError('allowed_mentions parameter must be AllowedMentions')

        self.allowed_mentions: Optional[AllowedMentions] = allowed_mentions
        self._chunk_requests: Dict[Union[int, str], ChunkRequest] = {}

        activity = options.get('activity', None)
        if activity:
            if not isinstance(activity, BaseActivity):
                raise TypeError('activity parameter must derive from BaseActivity.')

            activity = activity.to_dict()

        status = options.get('status', None)
        if status:
            if status is Status.offline:
                status = 'invisible'
            else:
                status = str(status)

        intents = options.get('intents', None)
        if intents is not None:
            if not isinstance(intents, Intents):
                raise TypeError(f'intents parameter must be Intent not {type(intents)!r}')
        else:
            intents = Intents.default()

        if not intents.guilds:
            _log.warning('Guilds intent seems to be disabled. This may cause state related issues.')

        self._chunk_guilds: bool = options.get('chunk_guilds_at_startup', intents.members)

        # Ensure these two are set properly
        if not intents.members and self._chunk_guilds:
            raise ValueError('Intents.members must be enabled to chunk guilds at startup.')

        cache_flags = options.get('member_cache_flags', None)
        if cache_flags is None:
            cache_flags = MemberCacheFlags.from_intents(intents)
        else:
            if not isinstance(cache_flags, MemberCacheFlags):
                raise TypeError(f'member_cache_flags parameter must be MemberCacheFlags not {type(cache_flags)!r}')

            cache_flags._verify_intents(intents)

        self.member_cache_flags: MemberCacheFlags = cache_flags
        self._activity: Optional[ActivityPayload] = activity
        self._status: Optional[str] = status
        self._intents: Intents = intents
        self._command_tree: Optional[CommandTree] = None
        self._translator: Optional[Translator] = None

        if not intents.members or cache_flags._empty:
            self.store_user = self.store_user_no_intents

        self.parsers: Dict[str, Callable[[Any], None]]
        self.parsers = parsers = {}
        for attr, func in inspect.getmembers(self):
            if attr.startswith('parse_'):
                parsers[attr[6:].upper()] = func

        self.clear()

    def _loads(self, value, decode):
        if value is None:
            return value

        if not decode:
            return value.decode("utf-8")

        try:
            return orjson.loads(value)
        except orjson.JSONDecodeError:
            return value.decode("utf-8")

    def _dumps(self, value):
        if isinstance(value, (str, int, float)):
            return value
        return orjson.dumps(value).decode("utf-8")

    async def delete(self, key):
        return await self.redis.delete(key)

    async def get(self, keys, decode=True):
        results = []
        if isinstance(keys, (list, tuple)):
            if len(keys) == 0:
                return []
            results.extend([self._loads(x, decode) for x in await self.redis.mget(*keys)])
        else:
            results.append(self._loads(await self.redis.get(keys), decode))

        for index, value in enumerate(results):
            if isinstance(value, dict):
                value["_key"] = keys[index] if isinstance(keys, (list, tuple)) else keys

                results[index] = value

        if isinstance(keys, (list, tuple)):
            return [x for x in results if x is not None]

        return results[0]

    async def expire(self, key, time):
        return await self.redis.expire(key, time)

    async def set(self, key, value=None):
        if isinstance(key, (list, tuple)):
            return await self.redis.mset(*key)

        return await self.redis.set(key, self._dumps(value))

    async def sadd(self, key, *value):
        return await self.redis.sadd(key, *[self._dumps(x) for x in value])

    async def srem(self, key, *value):
        return await self.redis.srem(key, *[self._dumps(x) for x in value])

    async def smembers(self, key, decode=True):
        return [self._loads(x, decode) for x in await self.redis.smembers(key)]

    async def sismember(self, key, value):
        return await self.redis.sismember(key, self._dumps(value))

    async def scard(self, key):
        return await self.redis.scard(key)

    async def _members(self, key, key_id=None):
        key += "_keys"

        if key_id:
            key += f":{key_id}"

        return [x.decode("utf-8") for x in await self.redis.smembers(key)]

    async def _members_get(
        self, key, key_id=None, name=None, first=None, second=None, predicate=None
    ):
        for match in await self._members(key, key_id):
            keys = match.split(":")
            if name is None or keys[0] == str(name):
                if first is None or (len(keys) >= 2 and keys[1] == str(first)):
                    if second is None or (len(keys) >= 3 and keys[2] == str(second)):
                        if predicate is None or predicate(match) is True:
                            return await self.get(match)

        return None

    async def _members_get_all(
        self, key, key_id=None, name=None, first=None, second=None, predicate=None
    ):
        matches = []
        for match in await self._members(key, key_id):
            keys = match.split(":")
            if name is None or keys[0] == str(name):
                if first is None or (len(keys) >= 1 and keys[1] == str(first)):
                    if second is None or (len(keys) >= 2 and keys[2] == str(second)):
                        if predicate is None or predicate(match) is True:
                            matches.append(match)

        return await self.get(matches)

    def _key_first(self, obj):
        keys = obj["_key"].split(":")
        return int(keys[1])

    async def _users(self):
        user_ids = set([x.split(":")[2] for x in await self._members("member")])
        return [User(state=self, data=x["user"]) for x in await self.get(user_ids)]

    async def _emojis(self):
        results = await self._members_get_all("emoji")
        emojis = []

        for result in results:
            guild = await self._get_guild(self._key_first(result))

            if guild:
                emojis.append(Emoji(guild=guild, state=self, data=result))

        return emojis

    async def _guilds(self):
        guilds = [Guild(state=self, data=x) for x in await self._members_get_all("guild")]
        return [x for x in guilds if not x.unavailable]

    async def _private_channels(self):
        return []

    async def _messages(self):
        messages = []
        for result in await self._members_get_all("message"):
            channel = await self.get_channel(int(result["channel_id"]))

            if channel:
                message = Message(channel=channel, state=self, data=result)
                messages.append(message)

        return messages

    def process_chunk_requests(self, guild_id, nonce, members, complete):
        return

    def call_handlers(self, key, *args, **kwargs):
        try:
            func = self.handlers[key]
        except KeyError:
            pass
        else:
            func(*args, **kwargs)

    async def call_hooks(self, key, *args, **kwargs):
        try:
            func = self.hooks[key]
        except KeyError:
            pass
        else:
            await func(*args, **kwargs)

    async def user(self):
        result = await self.get("bot_user")
        if result:
            return ClientUser(state=self, data=result)
        return None

    def self_id(self):
        return self.id

    @property
    def intents(self):
        return

    @property
    def voice_clients(self):
        return

    def _get_voice_client(self, guild_id):
        return

    def _add_voice_client(self, guild_id, voice):
        return

    def _remove_voice_client(self, guild_id):
        return

    def _update_references(self, ws):
        return

    def store_user(self, data):
        return User(state=self, data=data)
    
    def store_user_no_intents(self, data: Union[UserPayload, PartialUserPayload], *, cache: bool = True) -> User:
        return User(state=self, data=data)

    async def get_user(self, user_id):
        result = await self._members_get("member", second=user_id)

        if result:
            return User(state=self, data=result["user"])

        return None

    def store_emoji(self, guild, data):
        return Emoji(guild=guild, state=self, data=data)
    
    def store_sticker(self, guild: Guild, data: GuildStickerPayload) -> GuildSticker:
        return GuildSticker(state=self, data=data)
    
    def store_view(self, view: View, message_id: Optional[int] = None, interaction_id: Optional[int] = None) -> None:
        if interaction_id is not None:
            self._view_store.remove_interaction_mapping(interaction_id)
        self._view_store.add_view(view, message_id)

    def prevent_view_updates_for(self, message_id: int) -> Optional[View]:
        return self._view_store.remove_message_tracking(message_id)

    async def guilds(self):
        return await self._guilds()

    async def _get_guild(self, guild_id):
        result = await self.get(f"guild:{guild_id}")

        if result:
            guild = Guild(state=self, data=result)
            if not guild.unavailable:
                return guild

        return None
    
    def _get_or_create_unavailable_guild(self, guild_id: int) -> Guild:
        return self._guilds.get(guild_id) or Guild._create_unavailable(state=self, guild_id=guild_id)

    def _add_guild(self, guild):
        return

    def _remove_guild(self, guild):
        return

    async def emojis(self):
        return await self._emojis()

    async def get_emoji(self, emoji_id):
        result = await self._members_get("emoji", second=emoji_id)

        if result:
            guild = await self._get_guild(self._key_first(result))

            if guild:
                return Emoji(guild=guild, state=self, data=result)

        return None

    async def private_channels(self):
        return await self._private_channels()

    async def _get_private_channel(self, channel_id):
        result = await self._get_channel(channel_id)
        if result and isinstance(result, DMChannel):
            return result

        return None

    async def _get_private_channel_by_user(self, user_id):
        return utils.find(lambda x: x.recipient.id == user_id, await self.private_channels())

    def _add_private_channel(self, channel):
        return

    def add_dm_channel(self, data):
        return DMChannel(me=self.user, state=self, data=data)

    def _remove_private_channel(self, channel):
        return

    async def _get_message(self, msg_id):
        result = await self._members_get("message", second=msg_id)

        if result:
            channel = await self.get_channel(self._key_first(result))

            if channel:
                result = Message(channel=channel, state=self, data=result)

        return result

    def _add_guild_from_data(self, guild):
        return Guild(state=self, data=guild)

    def _guild_needs_chunking(self, guild):
        return

    async def _get_guild_channel(self, channel_id):
        result = await self._get_channel(channel_id)
        if result and not isinstance(result, DMChannel):
            return result

        return None

    async def chunker(self, guild_id, query="", limit=0, *, nonce=None):
        return

    async def query_members(self, guild, query, limit, user_ids, cache):
        return

    async def _delay_ready(self):
        try:
            while True:
                try:
                    guild = await asyncio.wait_for(
                        self._ready_state.get(), timeout=self._ready_timeout
                    )
                except asyncio.TimeoutError:
                    break
                else:
                    if guild.unavailable is False:
                        self.dispatch("guild_available", guild)
                    else:
                        self.dispatch("guild_join", guild)
            try:
                del self._ready_state
            except AttributeError:
                pass
        except asyncio.CancelledError:
            pass
        else:
            self.call_handlers("ready")
            self.dispatch("ready")
        finally:
            self._ready_task = None

    async def parse_ready(self, data, old):
        if self._ready_task is not None:
            self._ready_task.cancel()

        self.dispatch("connect")
        self._ready_state = asyncio.Queue()
        self._ready_task = asyncio.ensure_future(self._delay_ready(), loop=self.loop)

    async def parse_resumed(self, data, old):
        self.dispatch("resumed")

    async def parse_message_create(self, data, old):
        channel = await self.get_channel(int(data["channel_id"]))

        if not channel and not data.get("guild_id"):
            channel = DMChannel(me=await self.user(), state=self, data={"id": data["channel_id"]})

        if channel:
            message = self.create_message(channel=channel, data=data)
            self.dispatch("message", message)

    async def parse_message_delete(self, data, old):
        raw = RawMessageDeleteEvent(data)

        if old:
            channel = await self.get_channel(int(data["channel_id"]))
            if channel:
                old = self.create_message(channel=channel, data=old)
                raw.cached_message = old
                self.dispatch("message_delete", old)

        self.dispatch("raw_message_delete", raw)

    async def parse_message_delete_bulk(self, data, old):
        raw = RawBulkMessageDeleteEvent(data)

        if old:
            messages = []
            for old_message in old:
                channel = await self.get_channel(int(old_message["channel_id"]))
                if channel:
                    messages.append(self.create_message(channel=channel, data=old_message))

            raw.cached_messages = old
            self.dispatch("bulk_message_delete", old)

        self.dispatch("raw_bulk_message_delete", raw)

    async def parse_message_update(self, data, old):
        raw = RawMessageUpdateEvent(data)

        if old:
            channel = await self.get_channel(int(data["channel_id"]))
            if channel:
                old = self.create_message(channel=channel, data=old)
                raw.cached_message = old
                new = copy.copy(old)
                new._update(data)
                self.dispatch("message_edit", old, new)

        self.dispatch("raw_message_edit", raw)

    async def parse_message_reaction_add(self, data, old):
        emoji = PartialEmoji.with_state(
            self,
            id=utils._get_as_snowflake(data["emoji"], "id"),
            animated=data["emoji"].get("animated", False),
            name=data["emoji"]["name"],
        )

        raw = RawReactionActionEvent(data, emoji, "REACTION_ADD")

        member = data.get("member")
        if member:
            guild = await self._get_guild(raw.guild_id)
            if guild:
                raw.member = Member(guild=guild, state=self, data=member)

        self.dispatch("raw_reaction_add", raw)

        message = await self._get_message(raw.message_id)
        if message:
            reaction = Reaction(
                message=message, data=data, emoji=await self._upgrade_partial_emoji(emoji)
            )
            user = raw.member or await self._get_reaction_user(message.channel, raw.user_id)

            if user:
                self.dispatch("reaction_add", reaction, user)

    async def parse_message_reaction_remove_all(self, data, old):
        raw = RawReactionClearEvent(data)
        self.dispatch("raw_reaction_clear", raw)

        message = await self._get_message(raw.message_id)
        if message:
            self.dispatch("reaction_clear", message, None)

    async def parse_message_reaction_remove(self, data, old):
        emoji = PartialEmoji.with_state(
            self,
            id=utils._get_as_snowflake(data["emoji"], "id"),
            name=data["emoji"]["name"],
        )

        raw = RawReactionActionEvent(data, emoji, "REACTION_REMOVE")
        self.dispatch("raw_reaction_remove", raw)

        message = await self._get_message(raw.message_id)
        if message:
            reaction = Reaction(
                message=message, data=data, emoji=await self._upgrade_partial_emoji(emoji)
            )
            user = await self._get_reaction_user(message.channel, raw.user_id)

            if user:
                self.dispatch("reaction_remove", reaction, user)

    async def parse_message_reaction_remove_emoji(self, data, old):
        emoji = PartialEmoji.with_state(
            self,
            id=utils._get_as_snowflake(data["emoji"], "id"),
            name=data["emoji"]["name"],
        )

        raw = RawReactionClearEmojiEvent(data, emoji)
        self.dispatch("raw_reaction_clear_emoji", raw)

        message = await self._get_message(raw.message_id)
        if message:
            reaction = Reaction(
                message=message, data=data, emoji=await self._upgrade_partial_emoji(emoji)
            )
            self.dispatch("reaction_clear_emoji", reaction)

    async def parse_presence_update(self, data, old):
        guild = await self._get_guild(utils._get_as_snowflake(data, "guild_id"))

        if not guild:
            return

        old_member = None
        member = await guild.get_member(int(data["user"]["id"]))
        if member and old:
            old_member = Member._copy(member)
            user_update = old_member._presence_update(data=old, user=old["user"])

            if user_update:
                self.dispatch("user_update", user_update[1], user_update[0])

        self.dispatch("member_update", old_member, member)

    async def parse_user_update(self, data, old):
        return

    async def parse_invite_create(self, data, old):
        invite = Invite.from_gateway(state=self, data=data)
        self.dispatch("invite_create", invite)

    async def parse_invite_delete(self, data, old):
        invite = Invite.from_gateway(state=self, data=data)
        self.dispatch("invite_delete", invite)

    async def parse_channel_delete(self, data, old):
        if old and old["guild_id"]:
            guild = await self._get_guild(utils._get_as_snowflake(data, "guild_id"))
            if guild:
                factory, _ = _channel_factory(old["type"])
                channel = factory(guild=guild, state=self, data=old)
                self.dispatch("guild_channel_delete", channel)
        elif old:
            channel = DMChannel(me=self.user, state=self, data=old)
            self.dispatch("private_channel_delete", channel)

    async def parse_channel_update(self, data, old):
        channel_type = try_enum(ChannelType, data.get("type"))
        if old and channel_type is ChannelType.private:
            channel = DMChannel(me=self.user, state=self, data=data)
            old_channel = DMChannel(me=self.user, state=self, data=old)
            self.dispatch("private_channel_update", old_channel, channel)
        elif old:
            guild = await self._get_guild(utils._get_as_snowflake(data, "guild_id"))
            if guild:
                factory, _ = _channel_factory(data["type"])
                channel = factory(guild=guild, state=self, data=data)
                old_factory, _ = _channel_factory(old["type"])
                old_channel = old_factory(guild=guild, state=self, data=old)
                self.dispatch("guild_channel_update", old_channel, channel)

    async def parse_channel_create(self, data, old):
        factory, ch_type = _channel_factory(data["type"])
        if ch_type is ChannelType.private:
            channel = DMChannel(me=self.user, data=data, state=self)
            self.dispatch("private_channel_create", channel)
        else:
            guild = await self._get_guild(utils._get_as_snowflake(data, "guild_id"))
            if guild:
                channel = factory(guild=guild, state=self, data=data)
                self.dispatch("guild_channel_create", channel)

    async def parse_channel_pins_update(self, data, old):
        channel = await self.get_channel(int(data["channel_id"]))
        last_pin = (
            utils.parse_time(data["last_pin_timestamp"]) if data["last_pin_timestamp"] else None
        )

        try:
            channel.guild
        except AttributeError:
            self.dispatch("private_channel_pins_update", channel, last_pin)
        else:
            self.dispatch("guild_channel_pins_update", channel, last_pin)

    async def parse_channel_recipient_add(self, data, old):
        return

    async def parse_channel_recipient_remove(self, data, old):
        return

    async def parse_guild_member_add(self, data, old):
        guild = await self._get_guild(int(data["guild_id"]))
        if guild:
            member = Member(guild=guild, data=data, state=self)
            self.dispatch("member_join", member)

    async def parse_guild_member_remove(self, data, old):
        if old:
            guild = await self._get_guild(int(data["guild_id"]))
            if guild:
                member = Member(guild=guild, data=old, state=self)
                self.dispatch("member_remove", member)

    async def parse_guild_member_update(self, data, old):
        guild = await self._get_guild(int(data["guild_id"]))
        if old and guild:
            member = await guild.get_member(int(data["user"]["id"]))
            if member:
                old_member = Member._copy(member)
                old_member._update(old)
                user_update = old_member._update_inner_user(data["user"])

                if user_update:
                    self.dispatch("user_update", user_update[1], user_update[0])

                self.dispatch("member_update", old_member, member)

    async def parse_guild_emojis_update(self, data, old):
        guild = await self._get_guild(int(data["guild_id"]))
        if guild:
            before_emojis = None
            if old:
                before_emojis = [self.store_emoji(guild, x) for x in old]

            after_emojis = tuple(map(lambda x: self.store_emoji(guild, x), data["emojis"]))
            self.dispatch("guild_emojis_update", guild, before_emojis, after_emojis)

    def _get_create_guild(self, data):
        return self._add_guild_from_data(data)

    async def chunk_guild(self, guild, *, wait=True, cache=None):
        return

    async def _chunk_and_dispatch(self, guild, unavailable):
        return

    async def parse_guild_create(self, data, old):
        unavailable = data.get("unavailable")

        if unavailable is True:
            return

        guild = self._get_create_guild(data)
        try:
            self._ready_state.put_nowait(guild)
        except AttributeError:
            if unavailable is False:
                self.dispatch("guild_available", guild)
            else:
                self.dispatch("guild_join", guild)

    async def parse_guild_sync(self, data, old):
        return

    async def parse_guild_update(self, data, old):
        guild = await self._get_guild(int(data["id"]))
        if guild:
            old_guild = None

            if old:
                old_guild = copy.copy(guild)
                old_guild = old_guild._from_data(old)

            self.dispatch("guild_update", old_guild, guild)

    async def parse_guild_delete(self, data, old):
        if old:
            old = Guild(state=self, data=old)
            if data.get("unavailable", False):
                new = Guild(state=self, data=data)
                self.dispatch("guild_unavailable", new)
            else:
                self.dispatch("guild_remove", old)

    async def parse_guild_ban_add(self, data, old):
        guild = await self._get_guild(int(data["guild_id"]))
        if guild:
            user = self.store_user(data["user"])
            member = await guild.get_member(user.id) or user
            self.dispatch("member_ban", guild, member)

    async def parse_guild_ban_remove(self, data, old):
        guild = await self._get_guild(int(data["guild_id"]))
        if guild:
            self.dispatch("member_unban", guild, self.store_user(data["user"]))

    async def parse_guild_role_create(self, data, old):
        guild = await self._get_guild(int(data["guild_id"]))
        if guild:
            role = Role(guild=guild, state=self, data=data["role"])
            self.dispatch("guild_role_create", role)

    async def parse_guild_role_delete(self, data, old):
        if old:
            guild = await self._get_guild(int(data["guild_id"]))
            if guild:
                role = Role(guild=guild, state=self, data=old)
                self.dispatch("guild_role_delete", role)

    async def parse_guild_role_update(self, data, old):
        if old:
            guild = await self._get_guild(int(data["guild_id"]))
            if guild:
                role = Role(guild=guild, state=self, data=data["role"])
                old_role = Role(guild=guild, state=self, data=old)
                self.dispatch("guild_role_update", old_role, role)

    async def parse_guild_members_chunk(self, data, old):
        return

    async def parse_guild_integrations_update(self, data, old):
        guild = await self._get_guild(int(data["guild_id"]))
        if guild:
            self.dispatch("guild_integrations_update", guild)

    async def parse_webhooks_update(self, data, old):
        channel = await self._get_guild(int(data["channel_id"]))
        if channel:
            self.dispatch("webhooks_update", channel)

    async def parse_voice_state_update(self, data, old):
        guild = await self._get_guild(utils._get_as_snowflake(data, "guild_id"))
        if guild:
            member = await guild.get_member(int(data["user_id"]))
            if member:
                channel = await self.get_channel(utils._get_as_snowflake(data, "channel_id"))
                if channel:
                    before = None
                    after = VoiceState(data=data, channel=channel)
                    old_channel = await self.get_channel(old["channel_id"])

                    if old and old_channel:
                        before = VoiceState(data=data, channel=old_channel)

                    self.dispatch("voice_state_update", member, before, after)

    def parse_voice_server_update(self, data, old):
        return

    async def parse_typing_start(self, data, old):
        channel = await self._get_guild_channel(int(data["channel_id"]))
        if channel:
            member = None

            if isinstance(channel, DMChannel):
                member = channel.recipient
            elif isinstance(channel, TextChannel):
                guild = await self._get_guild(int(data["guild_id"]))
                if guild:
                    member = await guild.get_member(utils._get_as_snowflake(data, "user_id"))

            if member:
                self.dispatch(
                    "typing",
                    channel,
                    member,
                    datetime.datetime.utcfromtimestamp(data.get("timestamp")),
                )

    async def parse_relationship_add(self, data, old):
        return

    async def parse_relationship_remove(self, data, old):
        return

    async def _get_reaction_user(self, channel, user_id):
        if isinstance(channel, TextChannel):
            return await channel.guild.get_member(user_id)
        return await self.get_user(user_id)

    async def get_reaction_emoji(self, data):
        emoji_id = utils._get_as_snowflake(data, "id")

        if not emoji_id:
            return data["name"]

        return await self.get_emoji(emoji_id)

    async def _upgrade_partial_emoji(self, emoji):
        if not emoji.id:
            return emoji.name

        return await self.get_emoji(emoji.id)

    async def _get_channel(self, channel_id):
        result = await self.get(f"channel:{channel_id}")

        if result:
            if result.get("guild_id"):
                factory, _ = _channel_factory(result["type"])
                guild = await self._get_guild(result["guild_id"])

                if guild:
                    return factory(guild=guild, state=self, data=result)
            else:
                return DMChannel(me=self.user, state=self, data=result)

        return None

    async def get_channel(self, channel_id):
        if not channel_id:
            return None

        return await self._get_channel(channel_id)

    def create_message(self, *, channel, data):
        message = Message(state=self, channel=channel, data=data)
        return message

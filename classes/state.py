import asyncio
import copy
import datetime
import inspect
import logging
from redis import asyncio as aioredis
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
from discord import utils
from discord._types import ClientT
from discord.activity import BaseActivity
from discord.audit_logs import AuditLogEntry
from discord.automod import AutoModAction, AutoModRule
from discord.channel import *
from discord.channel import _channel_factory
from discord.emoji import Emoji
from discord.enums import ChannelType, Status, try_enum
from discord.flags import ApplicationFlags, Intents, MemberCacheFlags
from discord.guild import Guild
from discord.integrations import _integration_factory
from discord.interactions import Interaction
from discord.invite import Invite
from discord.member import Member
from discord.mentions import AllowedMentions
from discord.message import Message
from discord.partial_emoji import PartialEmoji
from discord.raw_models import *
from discord.role import Role
from discord.scheduled_event import ScheduledEvent
from discord.stage_instance import StageInstance
from discord.sticker import GuildSticker
from discord.threads import Thread, ThreadMember
from discord.ui.view import View, ViewStore
from discord.user import ClientUser, User

from discord import utils, state
from discord.abc import PrivateChannel, GuildChannel
from discord.channel import *
from discord.emoji import Emoji
from discord.enums import ChannelType, try_enum
from discord.invite import Invite
from discord.member import VoiceState, Member
from discord.partial_emoji import PartialEmoji
from discord.raw_models import (
    RawBulkMessageDeleteEvent,
    RawMessageDeleteEvent,
    RawMessageUpdateEvent,
    RawReactionActionEvent,
    RawReactionClearEmojiEvent,
    RawReactionClearEvent,
    RawMemberRemoveEvent
)
from discord.reaction import Reaction
from discord.role import Role
from discord.user import ClientUser, User

from discord.channel import DMChannel, PartialMessageable
from discord.guild import Guild
from discord.member import Member
from discord.message import Message

# if TYPE_CHECKING: 
#     from discord.types import gateway as gw
#     from discord.types.user import PartialUser as PartialUserPayload
#     from discord.types.user import User as UserPayload
#     T = TypeVar('T')
#     Channel = Union[GuildChannel, PrivateChannel, PartialMessageable]

log = logging.getLogger(__name__)



# Overriding AutoShardedConnectionState
# Replace built in cache with redis cache
# Overrides methods related to:
# Users, Guilds, Channels, Messages

class State(state.AutoShardedConnectionState):
    def __init__(
        self, *, dispatch, handlers, hooks, http, redis: aioredis.Redis = None, shard_count=None, id, **options
    ):
        super().__init__(dispatch=dispatch, handlers=handlers, hooks=hooks, http=http, **options)
        
        # self.loop = loop
        self.redis = redis
        self.shard_count = shard_count
        self.id = id
        
        
    def clear(self):
        self.user: Optional[ClientUser] = None
        
    
        
    ######### REDIS METHODS #########
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
            kvd = dict(list(zip(key[::2], key[1::2])))
            return await self.redis.mset(kvd)

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
    
    def _members(self, key, key_id=None):
        key += "_keys"

        if key_id:
            key += f":{key_id}"

        return [x.decode("utf-8") for x in self.redis.smembers(key)]
    
    def _members_get_all(
        self, key, key_id=None, name=None, first=None, second=None, predicate=None
    ):
        matches = []
        for match in self._members(key, key_id):
            keys = match.split(":")
            if name is None or keys[0] == str(name):
                if first is None or (len(keys) >= 1 and keys[1] == str(first)):
                    if second is None or (len(keys) >= 2 and keys[2] == str(second)):
                        if predicate is None or predicate(match) is True:
                            matches.append(match)

        return self.get(matches)
    
    ######### END REDIS METHODS #########
    
    # Lists of users, guilds, channel, messages
    def _users(self):
        user_ids = set([x.split(":")[2] for x in self._members("member")])
        return [User(state=self, data=x["user"]) for x in  self.get(user_ids)]

    def _guilds(self):
        guilds = [Guild(state=self, data=x) for x in self._members_get_all("guild")]
        return [x for x in guilds if not x.unavailable]
    
    def _private_channels(self):
        return []
    
    def _messages(self):
        messages = []
        for result in self._members_get_all("message"):
            channel = self.get_channel(int(result["channel_id"]))

            if channel:
                message = Message(channel=channel, state=self, data=result)
                messages.append(message)

        return messages

    # data: Union[UserPayload, PartialUserPayload]
    def store_user(self, data, *, cache: bool = True) -> User:
        if cache:
            user_id = int(data["id"])
            self.set(f"user:{user_id}", data)
        return User(state=self, data=data)
    
    def get_user(self, id: int) -> Optional[User]:
        return self.get(f"user:{id}")
            
    
    @property
    def guilds(self) -> Sequence[Guild]:
        return self._guilds()
    
    def _get_guild(self, guild_id: Optional[int]) -> Optional[Guild]:
        return self.get(f"guild:{guild_id}")
    
    def _get_or_create_unavailable_guild(self, guild_id: int) -> Guild:
        return self.get(f"guild:guild_id") or Guild._create_unavailable(state=self, guild_id=guild_id)
    
    def _add_guild(self, guild: Guild) -> None:
        self.set(f"guild:{guild.id}", guild)
        
    def _remove_guild(self, guild: Guild) -> None:
        self.remove(f"guild:{guild.id}")
        super()._remove_guild(guild)
        
    # Update Guild in Redis Cache after receiving Event
    # The below functions are exactly the same as super() equivalents
    # Except they have to re-add the guild to the cache
    
    # data: gw.GuildMemberAddEvent
    def parse_guild_member_add(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            # _log.debug('GUILD_MEMBER_ADD referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        member = Member(guild=guild, data=data, state=self)
        if self.member_cache_flags.joined:
            guild._add_member(member)
            

        # if guild._member_count is not None:
        #     guild._member_count += 1
        self.set(f"guild:{guild.id}", guild)
        self.dispatch('member_join', member)
    
    # data: gw.GuildMemberRemoveEvent
    def parse_guild_member_remove(self, data) -> None:
        user = self.store_user(data['user'])
        raw = RawMemberRemoveEvent(data, user)

        guild = self._get_guild(raw.guild_id)
        if guild is not None:
            # if guild._member_count is not None:
            #     guild._member_count -= 1

            member = guild.get_member(user.id)
            if member is not None:
                raw.user = member
                guild._remove_member(member)
                self.dispatch('member_remove', member)
                
            self.set(f"guild:{guild.id}", guild) # Add Guild to Cache
            
        # else:
        #     _log.debug('GUILD_MEMBER_REMOVE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
        self.dispatch('raw_member_remove', raw)
    
    # data: gw.GuildMemberUpdateEvent
    def parse_guild_member_update(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        user = data['user']
        user_id = int(user['id'])
        if guild is None:
            # _log.debug('GUILD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        member = guild.get_member(user_id)
        if member is not None:
            old_member = Member._copy(member)
            member._update(data)
            user_update = member._update_inner_user(user)
            if user_update:
                self.dispatch('user_update', user_update[0], user_update[1])

            self.dispatch('member_update', old_member, member)
        else:
            if self.member_cache_flags.joined:
                member = Member(data=data, guild=guild, state=self)  # type: ignore # the data is not complete, contains a delta of values

                # Force an update on the inner user if necessary
                user_update = member._update_inner_user(user)
                if user_update:
                    self.dispatch('user_update', user_update[0], user_update[1])

                guild._add_member(member)
                self.set(f"guild:{guild.id}", guild) # Add Guild to Cache
                
            # _log.debug('GUILD_MEMBER_UPDATE referencing an unknown member ID: %s. Discarding.', user_id)
    
    # data: gw.GuildRoleCreateEvent
    def parse_guild_role_create(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            # _log.debug('GUILD_ROLE_CREATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        role_data = data['role']
        role = Role(guild=guild, data=role_data, state=self)
        guild._add_role(role)
        self.set(f"guild:{guild.id}", guild) # Update Guild in Cache
        self.dispatch('guild_role_create', role)
    
    # data: gw.GuildRoleDeleteEvent
    def parse_guild_role_delete(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            role_id = int(data['role_id'])
            try:
                role = guild._remove_role(role_id)
            except KeyError:
                return
            else:
                self.set(f"guild:{guild.id}", guild) # Update Guild in Cache
                self.dispatch('guild_role_delete', role)
        # else:
        #     _log.debug('GUILD_ROLE_DELETE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    # data: gw.GuildRoleUpdateEven
    def parse_guild_role_update(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            role_data = data['role']
            role_id = int(role_data['id'])
            role = guild.get_role(role_id)
            if role is not None:
                old_role = copy.copy(role)
                role._update(role_data)
                self.set(f"guild:{guild.id}", guild) # Update Guild in Cache
                self.dispatch('guild_role_update', old_role, role)
        # else:
        #     _log.debug('GUILD_ROLE_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])


 ########## GUILD DONE ##########

 ########## CHANNEL START ##########
    async def private_channels(self) -> Sequence[PrivateChannel]:
            channels = [x for x in self._members_get_all("pm")]
            return channels
        
    def _get_private_channel(self, channel_id: Optional[int]) -> Optional[PrivateChannel]:
        return self.get(f"pm:{channel_id}")

    def _get_private_channel_by_user(self, user_id: Optional[int]) -> Optional[DMChannel]:
        return self.get(f"pmUser:{user_id}")
        
    def _add_private_channel(self, channel: PrivateChannel) -> None:
        self.set(f"pm:{channel.id}", channel)
        
        if isinstance(channel, DMChannel) and channel.recipient:
            self.set(f"pmUser:{channel.recipient.id}", channel)
            
    def _remove_private_channel(self, channel: PrivateChannel) -> None:
        channel = self.get(f"pm:{channel.id}")
        self.delete(f"pm:{channel.id}")
        if channel is not None and isinstance(channel, DMChannel) and channel.recipient:
            self.remove(f"pmUser:{channel.recipient.id}")
            
 ########## CHANNEL DONE ##########

 ########## MESSAGE START ##########
    def _add_message(self, message: Message) -> None:
        self.set(f"message:{message.id}", message)
        
    def _remove_message(self, message: Message) -> None:
        self.delete(f"message:{message.id}")
        
    def _get_message(self, message_id: Optional[int]) -> Optional[Message]:
        return self.get(f"message:{message_id}")
    
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
    
   
    

   
        
    
    

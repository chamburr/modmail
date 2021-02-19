import asyncio
import logging
import time

import discord.abc

from discord import channel, utils
from discord.channel import DMChannel, GroupChannel, StoreChannel, VoiceChannel, _single_delete_strategy
from discord.enums import ChannelType, try_enum
from discord.errors import ClientException, InvalidArgument, NoMoreItems
from discord.permissions import Permissions

log = logging.getLogger(__name__)


class TextChannel(channel.TextChannel):
    def __init__(self, *, state, guild, data):
        self._state = state
        self.id = int(data["id"])
        self._type = data["type"]
        self._update(guild, data)

    def _update(self, guild, data):
        self.guild = guild
        self.name = data["name"]
        self.category_id = utils._get_as_snowflake(data, "parent_id")
        self.topic = data.get("topic")
        self.position = data["position"]
        self.nsfw = data.get("nsfw", False)
        self.slowmode_delay = data.get("rate_limit_per_user", 0)
        self._type = data.get("type", self._type)
        self.last_message_id = utils._get_as_snowflake(data, "last_message_id")
        self._fill_overwrites(data)

    def _fill_overwrites(self, data):
        self._overwrites = []
        everyone_index = 0
        everyone_id = self.guild.id

        for index, overridden in enumerate(data.get("permission_overwrites", [])):
            overridden_id = int(overridden.pop("id"))
            if overridden["type"] == 0:
                overridden["type"] = "role"
            elif overridden["type"] == 1:
                overridden["type"] = "member"
            self._overwrites.append(discord.abc._Overwrites(id=overridden_id, **overridden))

            if overridden["type"] == "member":
                continue

            if overridden_id == everyone_id:
                everyone_index = index

        tmp = self._overwrites
        if tmp:
            tmp[everyone_index], tmp[0] = tmp[0], tmp[everyone_index]

    async def _get_channel(self):
        return self

    @property
    def type(self):
        return try_enum(ChannelType, self._type)

    @property
    def _sorting_bucket(self):
        return ChannelType.text.value

    async def _permissions_for(self, member):
        if self.guild.owner_id == member.id:
            return Permissions.all()

        default = await self.guild.default_role()
        base = Permissions(default.permissions.value)
        roles = member._roles
        get_role = self.guild.get_role

        for role_id in roles:
            role = await get_role(role_id)
            if role is not None:
                base.value |= role._permissions

        if base.administrator:
            return Permissions.all()

        try:
            maybe_everyone = self._overwrites[0]
            if maybe_everyone.id == self.guild.id:
                base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
                remaining_overwrites = self._overwrites[1:]
            else:
                remaining_overwrites = self._overwrites
        except IndexError:
            remaining_overwrites = self._overwrites

        denies = 0
        allows = 0

        for overwrite in remaining_overwrites:
            if overwrite.type == "role" and roles.has(overwrite.id):
                denies |= overwrite.deny
                allows |= overwrite.allow

        base.handle_overwrite(allow=allows, deny=denies)

        for overwrite in remaining_overwrites:
            if overwrite.type == "member" and overwrite.id == member.id:
                base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)
                break

        if not base.send_messages:
            base.send_tts_messages = False
            base.mention_everyone = False
            base.embed_links = False
            base.attach_files = False

        if not base.read_messages:
            denied = Permissions.all_channel()
            base.value &= ~denied.value

        return base

    async def permissions_for(self, member):
        base = await self._permissions_for(member)

        denied = Permissions.voice()
        base.value &= ~denied.value
        return base

    @property
    def members(self):
        return [m for m in self.guild.members if self.permissions_for(m).read_messages]

    def is_nsfw(self):
        return self.nsfw

    def is_news(self):
        return self._type == ChannelType.news.value

    @property
    def last_message(self):
        return self._state._get_message(self.last_message_id) if self.last_message_id else None

    async def edit(self, *, reason=None, **options):
        await self._edit(options, reason=reason)

    async def clone(self, *, name=None, reason=None):
        return await self._clone_impl(
            {"topic": self.topic, "nsfw": self.nsfw, "rate_limit_per_user": self.slowmode_delay},
            name=name,
            reason=reason,
        )

    clone.__doc__ = discord.abc.GuildChannel.clone.__doc__

    async def delete_messages(self, messages):
        if not isinstance(messages, (list, tuple)):
            messages = list(messages)

        if len(messages) == 0:
            return

        if len(messages) == 1:
            message_id = messages[0].id
            await self._state.http.delete_message(self.id, message_id)
            return

        if len(messages) > 100:
            raise ClientException("Can only bulk delete messages up to 100 messages")

        message_ids = [m.id for m in messages]
        await self._state.http.delete_messages(self.id, message_ids)

    async def purge(
        self, *, limit=100, check=None, before=None, after=None, around=None, oldest_first=False, bulk=True
    ):
        if check is None:
            check = lambda m: True

        iterator = self.history(limit=limit, before=before, after=after, oldest_first=oldest_first, around=around)
        ret = []
        count = 0

        minimum_time = int((time.time() - 14 * 24 * 60 * 60) * 1000.0 - 1420070400000) << 22
        strategy = self.delete_messages if self._state.is_bot and bulk else _single_delete_strategy

        while True:
            try:
                msg = await iterator.next()
            except NoMoreItems:
                if count >= 2:
                    to_delete = ret[-count:]
                    await strategy(to_delete)
                elif count == 1:
                    await ret[-1].delete()

                return ret
            else:
                if count == 100:
                    to_delete = ret[-100:]
                    await strategy(to_delete)
                    count = 0
                    await asyncio.sleep(1)

                if check(msg):
                    if msg.id < minimum_time:
                        if count == 1:
                            await ret[-1].delete()
                        elif count >= 2:
                            to_delete = ret[-count:]
                            await strategy(to_delete)

                        count = 0
                        strategy = _single_delete_strategy

                    count += 1
                    ret.append(msg)

    async def webhooks(self):
        from discord.webhook import Webhook

        data = await self._state.http.channel_webhooks(self.id)
        return [Webhook.from_state(d, state=self._state) for d in data]

    async def create_webhook(self, *, name, avatar=None, reason=None):
        from discord.webhook import Webhook

        if avatar is not None:
            avatar = utils._bytes_to_base64_data(avatar)

        data = await self._state.http.create_webhook(self.id, name=str(name), avatar=avatar, reason=reason)
        return Webhook.from_state(data, state=self._state)

    async def follow(self, *, destination, reason=None):
        if not self.is_news():
            raise ClientException("The channel must be a news channel.")

        if not isinstance(destination, TextChannel):
            raise InvalidArgument("Expected TextChannel received {0.__name__}".format(type(destination)))

        from discord.webhook import Webhook

        data = await self._state.http.follow_webhook(self.id, webhook_channel_id=destination.id, reason=reason)
        return Webhook._as_follower(data, channel=destination, user=self._state.user)

    def get_partial_message(self, message_id):
        from discord.message import PartialMessage

        return PartialMessage(channel=self, id=message_id)


class CategoryChannel(channel.CategoryChannel):
    def _fill_overwrites(self, data):
        self._overwrites = []
        everyone_index = 0
        everyone_id = self.guild.id

        for index, overridden in enumerate(data.get("permission_overwrites", [])):
            overridden_id = int(overridden.pop("id"))
            if overridden["type"] == 0:
                overridden["type"] = "role"
            elif overridden["type"] == 1:
                overridden["type"] = "member"
            self._overwrites.append(discord.abc._Overwrites(id=overridden_id, **overridden))

            if overridden["type"] == "member":
                continue

            if overridden_id == everyone_id:
                everyone_index = index

        tmp = self._overwrites
        if tmp:
            tmp[everyone_index], tmp[0] = tmp[0], tmp[everyone_index]


def _channel_factory(channel_type):
    value = try_enum(ChannelType, channel_type)
    if value is ChannelType.text:
        return TextChannel, value
    elif value is ChannelType.voice:
        return VoiceChannel, value
    elif value is ChannelType.private:
        return DMChannel, value
    elif value is ChannelType.category:
        return CategoryChannel, value
    elif value is ChannelType.group:
        return GroupChannel, value
    elif value is ChannelType.news:
        return TextChannel, value
    elif value is ChannelType.store:
        return StoreChannel, value
    else:
        return None, value

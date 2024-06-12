import logging

from discord import channel, utils
from discord.channel import CategoryChannel, GroupChannel, StageChannel,  VoiceChannel
from discord.enums import ChannelType, try_enum
from discord.permissions import Permissions

from classes.embed import Embed
from discord.invite import Invite

log = logging.getLogger(__name__)


class TextChannel(channel.TextChannel):
    def __init__(self, *, state, guild, data):
        self._state = state
        self.id = int(data["id"])
        self._type = data.get("type", 0)
        self._update(guild, data)

    def _update(self, guild, data):
        self.guild = guild
        self.name = data.get("name", "")
        self.category_id = utils._get_as_snowflake(data, "parent_id")
        self.topic = data.get("topic", "")
        self.position = data.get("position", 0)
        self.nsfw = data.get("nsfw", False)
        self.slowmode_delay = data.get("rate_limit_per_user", 0)
        self._type = data.get("type", self._type)
        self.last_message_id = utils._get_as_snowflake(data, "last_message_id")
        self._fill_overwrites(data)

    async def create_invite(self, *, reason=None, **fields):
        data = await self._state.http.create_invite(self.id, reason=reason, **fields)
        return await Invite.from_incomplete(data=data, state=self._state)

    async def _permissions_for(self, member):
        if self.guild.owner_id == member.id:
            return Permissions.all()

        default = await self.guild.default_role()
        base = Permissions(default.permissions.value)
        roles = await self.guild.roles()

        for role in roles:
            if role.id in member._roles:
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
            if overwrite.is_role() and overwrite.id in [x.id for x in roles]:
                denies |= overwrite.deny
                allows |= overwrite.allow

        base.handle_overwrite(allow=allows, deny=denies)

        for overwrite in remaining_overwrites:
            if overwrite.is_member() and overwrite.id == member.id:
                base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)
                break

        if not base.read_messages:
            denied = Permissions.all_channel()
            base.value &= ~denied.value

        return base

    async def permissions_for(self, member):
        base = await self._permissions_for(member)

        denied = Permissions.voice()
        base.value &= ~denied.value

        return base

    async def send(self, content=None, **kwargs):
        if isinstance(content, Embed):
            return await super().send(embed=content, **kwargs)
        return await super().send(content, **kwargs)


class DMChannel(channel.DMChannel):
    def __init__(self, *, me, state, data):
        self._state = state
        self.recipient = None
        self.me = me
        self.id = int(data["id"])

    async def send(self, content=None, **kwargs):
        if isinstance(content, Embed):
            return await super().send(embed=content, **kwargs)
        return await super().send(content, **kwargs)


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
    elif value is ChannelType.stage_voice:
        return StageChannel, value
    else:
        return TextChannel, value

import logging

from discord import guild, utils
from discord.channel import CategoryChannel
from discord.emoji import Emoji
from discord.enums import (
    ChannelType,
    ContentFilter,
    NotificationLevel,
    VerificationLevel,
    VoiceRegion,
    try_enum,
)
from discord.member import VoiceState
from discord.role import Role

from classes.channel import TextChannel, _channel_factory
from classes.invite import Invite
from classes.member import Member
from utils import tools

log = logging.getLogger(__name__)


class Guild(guild.Guild):
    def __init__(self, *, data, state):
        self._state = state
        self._from_data(data)

    def _add_channel(self, channel):
        return

    def _remove_channel(self, channel):
        return

    def _add_member(self, member):
        return

    def _remove_member(self, member):
        return

    def _update_voice_state(self, data, channel_id):
        return

    def _add_role(self, role):
        return

    def _remove_role(self, role_id):
        return

    def _from_data(self, guild):
        member_count = guild.get("member_count", None)
        if member_count is not None:
            self._member_count = member_count

        self.name = guild.get("name")
        self.region = try_enum(VoiceRegion, guild.get("region"))
        self.verification_level = try_enum(VerificationLevel, guild.get("verification_level"))
        self.default_notifications = try_enum(
            NotificationLevel, guild.get("default_message_notifications")
        )
        self.explicit_content_filter = try_enum(
            ContentFilter, guild.get("explicit_content_filter", 0)
        )
        self.afk_timeout = guild.get("afk_timeout")
        self.icon = guild.get("icon")
        self.banner = guild.get("banner")
        self.unavailable = guild.get("unavailable", False)
        self.id = int(guild["id"])
        self.mfa_level = guild.get("mfa_level")
        self.features = guild.get("features", [])
        self.splash = guild.get("splash")
        self._system_channel_id = utils._get_as_snowflake(guild, "system_channel_id")
        self.description = guild.get("description")
        self.max_presences = guild.get("max_presences")
        self.max_members = guild.get("max_members")
        self.max_video_channel_users = guild.get("max_video_channel_users")
        self.premium_tier = guild.get("premium_tier", 0)
        self.premium_subscription_count = guild.get("premium_subscription_count") or 0
        self._system_channel_flags = guild.get("system_channel_flags", 0)
        self.preferred_locale = guild.get("preferred_locale")
        self.discovery_splash = guild.get("discovery_splash")
        self._rules_channel_id = utils._get_as_snowflake(guild, "rules_channel_id")
        self._public_updates_channel_id = utils._get_as_snowflake(
            guild, "public_updates_channel_id"
        )
        self._large = None if member_count is None else self._member_count >= 250
        self.owner_id = utils._get_as_snowflake(guild, "owner_id")
        self._afk_channel_id = utils._get_as_snowflake(guild, "afk_channel_id")

    async def create_text_channel(
        self, name, *, overwrites=None, category=None, reason=None, **options
    ):
        data = await self._create_channel(
            name, overwrites, ChannelType.text, category, reason=reason, **options
        )
        return TextChannel(state=self._state, guild=self, data=data)

    async def create_category(self, name, *, overwrites=None, reason=None, position=None):
        data = await self._create_channel(
            name, overwrites, ChannelType.category, reason=reason, position=position
        )
        return CategoryChannel(state=self._state, guild=self, data=data)

    async def fetch_member(self, member_id):
        data = await self._state.http.get_member(self.id, member_id)
        return Member(data=data, state=self._state, guild=self)

    async def _channels(self):
        channels = []
        for channel in await self._state._members_get_all("guild", key_id=self.id, name="channel"):
            factory, _ = _channel_factory(channel["type"])
            channels.append(
                factory(guild=self, state=self._state, data=tools.upgrade_payload(channel))
            )

        return channels

    async def _emojis(self):
        return [
            Emoji(guild=self, state=self._state, data=x)
            for x in await self._state._members_get_all("guild", key_id=self.id, name="emoji")
        ]

    async def _members(self):
        return [
            Member(guild=self, state=self._state, data=x)
            for x in await self._state._members_get_all("guild", key_id=self.id, name="member")
        ]

    async def _roles(self):
        return sorted(
            [
                Role(guild=self, state=self._state, data=tools.upgrade_payload(x))
                for x in await self._state._members_get_all("guild", key_id=self.id, name="role")
            ]
        )

    async def _voice_states(self):
        voices = []
        for voice in await self._state._members_get_all("guild", key_id=self.id, name="voice"):
            if voice["channel_id"]:
                channel = await self.get_channel(int(voice["channel_id"]))
                if channel:
                    voices.append(VoiceState(channel=channel, data=voice))
            else:
                voices.append(VoiceState(channel=None, data=voice))
        return voices

    async def _voice_state_for(self, user_id):
        state = await self._state.get(f"voice:{self.id}:{user_id}")
        if state and state["channel_id"]:
            channel = await self.get_channel(int(state["channel_id"]))
            if channel:
                return VoiceState(channel=channel, data=state)
        elif state:
            return VoiceState(channel=None, data=state)
        return None

    async def channels(self):
        return await self._channels()

    async def text_channels(self):
        channels = [x for x in await self._channels() if isinstance(x, TextChannel)]
        channels.sort(key=lambda x: (x.position, x.id))
        return channels

    async def get_channel(self, channel_id):
        channel = await self._state.get(f"channel:{channel_id}")

        if not channel:
            return None

        factory, _ = _channel_factory(channel["type"])
        return factory(guild=self, state=self._state, data=channel)

    async def afk_channel(self):
        channel_id = self._afk_channel_id
        return channel_id and await self.get_channel(channel_id)

    async def system_channel(self):
        channel_id = self._system_channel_id
        return channel_id and await self.get_channel(channel_id)

    async def rules_channel(self):
        channel_id = self._rules_channel_id
        return channel_id and await self.get_channel(channel_id)

    async def public_updates_channel(self):
        channel_id = self._public_updates_channel_id
        return channel_id and await self.get_channel(channel_id)

    async def emojis(self):
        return await self._emojis()

    async def members(self):
        return await self._members()

    async def get_member(self, user_id):
        member = await self._state.get(f"member:{self.id}:{user_id}")

        if member:
            return Member(guild=self, state=self._state, data=member)

        return None

    async def me(self):
        member = await self.get_member(self._state.id)

        if member:
            return member

        return await self.fetch_member(self._state.id)

    async def roles(self):
        return await self._roles()

    async def get_role(self, role_id):
        role = await self._state.get(f"role:{self.id}:{role_id}")

        if role:
            return Role(guild=self, state=self._state, data=tools.upgrade_payload(role))

        return None

    async def default_role(self):
        return await self.get_role(self.id)

    async def invites(self):
        data = await self._state.http.invites_from(self.id)
        result = []
        for invite in data:
            channel = await self.get_channel(int(invite["channel"]["id"]))
            invite["channel"] = channel
            invite["guild"] = self
            result.append(Invite(state=self._state, data=invite))

        return result

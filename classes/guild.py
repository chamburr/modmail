import logging

from discord import CategoryChannel, InvalidArgument, PermissionOverwrite, guild, utils
from discord.enums import *
from discord.enums import try_enum
from discord.member import Member, VoiceState
from discord.role import Role

from classes.channel import TextChannel, _channel_factory

log = logging.getLogger(__name__)


class Guild(guild.Guild):
    def __init__(self, *, data, state):
        self._state = state
        self._from_data(data)

    async def default_role(self):
        return await self.get_role(self.id)

    async def me(self):
        self_id = (await self._state.user()).id
        return await self.get_member(self_id)

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
        self.default_notifications = try_enum(NotificationLevel, guild.get("default_message_notifications"))
        self.explicit_content_filter = try_enum(ContentFilter, guild.get("explicit_content_filter", 0))
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
        self._public_updates_channel_id = utils._get_as_snowflake(guild, "public_updates_channel_id")
        self._large = None if member_count is None else self._member_count >= 250
        self.owner_id = utils._get_as_snowflake(guild, "owner_id")
        self._afk_channel_id = utils._get_as_snowflake(guild, "afk_channel_id")

    async def _create_channel(self, name, overwrites, channel_type, category=None, **options):
        if overwrites is None:
            overwrites = {}
        elif not isinstance(overwrites, dict):
            raise InvalidArgument("overwrites parameter expects a dict.")

        perms = []
        for target, perm in overwrites.items():
            if not isinstance(perm, PermissionOverwrite):
                raise InvalidArgument("Expected PermissionOverwrite received {0.__name__}".format(type(perm)))

            allow, deny = perm.pair()
            payload = {"allow": allow.value, "deny": deny.value, "id": target.id}

            if isinstance(target, Role):
                payload["type"] = "role"
            else:
                payload["type"] = "member"

            perms.append(payload)

        try:
            options["rate_limit_per_user"] = options.pop("slowmode_delay")
        except KeyError:
            pass

        parent_id = category.id if category else None
        return await self._state.http.create_channel(
            self.id, channel_type.value, name=name, parent_id=parent_id, permission_overwrites=perms, **options
        )

    async def create_text_channel(self, name, *, overwrites=None, category=None, reason=None, **options):
        data = await self._create_channel(name, overwrites, ChannelType.text, category, reason=reason, **options)
        channel = TextChannel(state=self._state, guild=self, data=data)

        return channel

    async def create_category(self, name, *, overwrites=None, reason=None, position=None):
        data = await self._create_channel(name, overwrites, ChannelType.category, reason=reason, position=position)
        channel = CategoryChannel(state=self._state, guild=self, data=data)

        return channel

    create_category_channel = create_category

    async def _channels(self):
        channels = []
        for channel in await self._state._members_get_all("guild", key_id=self.id, name="channel"):
            factory, _ = _channel_factory(channel["type"])
            channels.append(factory(guild=self, state=self._state, data=channel))
        return channels

    async def _members(self):
        members = []
        for member in await self._state._members_get_all("guild", key_id=self.id, name="member"):
            members.append(Member(guild=self, state=self._state, data=member))
        return members

    async def _roles(self):
        roles = []
        for role in await self._state._members_get_all("guild", key_id=self.id, name="role"):
            roles.append(Role(guild=self, state=self._state, data=role))
        return roles

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
        result = await self._state._get(f"voice:{self.id}:{user_id}")
        if result and result["channel_id"]:
            channel = await self.get_channel(int(result["channel_id"]))
            if channel:
                result = VoiceState(channel=channel, data=result)
        elif result:
            result = VoiceState(channel=None, data=result)
        return result

    async def channels(self):
        return await self._channels()

    async def get_channel(self, channel_id):
        result = await self._state._get(f"channel:{self.id}:{channel_id}")
        if not result:
            return None
        factory, _ = _channel_factory(result["type"])
        return factory(guild=self, state=self._state, data=result)

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

    async def members(self):
        return await self._members()

    async def get_member(self, user_id):
        result = await self._state._get(f"member:{self.id}:{user_id}")
        if result:
            result = Member(guild=self, state=self._state, data=result)
        return result

    async def roles(self):
        return await self._roles()

    async def get_role(self, role_id):
        result = await self._state._get(f"role:{self.id}:{role_id}")
        if result:
            result["permissions"] = int(result["permissions"])
            result = Role(guild=self, state=self._state, data=result)
        return result

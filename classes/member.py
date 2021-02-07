import logging
import sys

from discord import member
from discord.activity import create_activity
from discord.utils import parse_time

log = logging.getLogger(__name__)


class Member(member.Member):
    def __init__(self, *, data, guild, state):
        self._state = state
        self._user = state.store_user(data["user"])
        self.guild = guild
        self.joined_at = parse_time(data.get("joined_at"))
        self.premium_since = parse_time(data.get("premium_since"))
        self._update_roles(data)
        self.nick = data.get("nick", None)

    async def _presence(self):
        return await self._state._get(f"presence:{self.guild.id}:{self._user.id}") or {}

    async def activities(self):
        return tuple(map(create_activity, (await self._presence()).get("activities", [])))

    async def _client_status(self):
        presence = await self._presence()
        status = {sys.intern(x): sys.intern(y) for x, y in presence.get("client_status", {}).items()}
        status[None] = sys.intern(presence["status"]) if presence.get("status") else "offline"
        return status

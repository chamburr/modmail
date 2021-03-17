import logging
import sys

from discord import member, utils
from discord.activity import create_activity

log = logging.getLogger(__name__)


class Member(member.Member):
    def __init__(self, *, data, guild, state):
        self._state = state
        self._user = state.store_user(data["user"])
        self.guild = guild
        self.joined_at = utils.parse_time(data.get("joined_at"))
        self.premium_since = utils.parse_time(data.get("premium_since"))
        self._update_roles(data)
        self.nick = data.get("nick", None)

    async def roles(self):
        roles = [x for x in await self.guild.roles() if x in self._roles]
        roles.append(await self.guild.default_role())
        roles.sort()
        return roles

    async def _presence(self):
        return await self._state._get(f"presence:{self.guild.id}:{self._user.id}") or {}

    async def activities(self):
        return tuple(map(create_activity, (await self._presence()).get("activities", [])))

    async def _client_status(self):
        presence = await self._presence()
        status = {sys.intern(x): sys.intern(y) for x, y in presence.get("client_status", {}).items()}
        status[None] = sys.intern(presence["status"]) if presence.get("status") else "offline"
        return status

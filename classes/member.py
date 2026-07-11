from __future__ import annotations

import logging
import sys

from typing import TYPE_CHECKING, Any

from discord import Permissions, Role, Status, member, utils
from discord.activity import create_activity
from discord.enums import try_enum

if TYPE_CHECKING:
    from discord.activity import ActivityTypes

    from classes.guild import Guild
    from classes.state import State

log = logging.getLogger(__name__)


class Member(member.Member):
    def __init__(self, *, data: dict[str, Any], guild: Guild, state: State) -> None:
        self._state = state
        self._user = state.store_user(data["user"])
        self.guild = guild
        self.joined_at = utils.parse_time(data.get("joined_at"))
        self.premium_since = utils.parse_time(data.get("premium_since"))
        self._roles = utils.SnowflakeList(map(int, data.get("roles", [])))
        self.nick = data.get("nick", None)
        self._avatar = data.get("user", {}).get("avatar")

    async def guild_permissions(
        self,
    ) -> Permissions:
        if self.guild.owner_id == self.id:
            return Permissions.all()

        base = Permissions.none()
        for role in await self.roles():
            base.value |= role._permissions

        if base.administrator:
            return Permissions.all()

        return base

    async def roles(self) -> list[Role]:
        roles = [x for x in await self.guild.roles() if x.id in self._roles]
        roles.append(await self.guild.default_role())
        roles.sort()
        return roles

    async def _presence(self) -> dict[str, Any]:
        return await self._state.get(f"presence:{self.guild.id}:{self._user.id}") or {}

    async def activities(
        self,
    ) -> tuple[ActivityTypes, ...]:
        return tuple(
            create_activity(x, self._state) for x in (await self._presence()).get("activities", [])
        )

    async def _client_status(self) -> dict[str | None, str]:
        presence = await self._presence()
        status: dict[str | None, str] = {
            sys.intern(x): sys.intern(y) for x, y in presence.get("client_status", {}).items()
        }
        status[None] = sys.intern(presence["status"]) if presence.get("status") else "offline"
        return status

    async def status(self) -> Status:
        return try_enum(Status, await self._client_status())

    async def is_on_mobile(self) -> bool:
        return "member" in await self._client_status()

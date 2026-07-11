from __future__ import annotations

import logging

from typing import TYPE_CHECKING, Any

from discord import http
from discord.http import Route

if TYPE_CHECKING:
    from discord.http import Response

log = logging.getLogger(__name__)


class HTTPClient(http.HTTPClient):
    def request_guild_members(
        self, guild_id: int, query: str, limit: int = 1
    ) -> Response[list[dict[str, Any]]]:
        return self.request(
            Route(
                "GET",
                "/guilds/{guild_id}/members/search?query={query}&limit={limit}",
                guild_id=guild_id,
                query=query,
                limit=limit,
            )
        )

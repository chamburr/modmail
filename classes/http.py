import logging

from discord import http
from discord.http import Route

log = logging.getLogger(__name__)


class HTTPClient(http.HTTPClient):
    def request_guild_members(self, guild_id, query, limit=1):
        return self.request(
            Route(
                "GET",
                "/guilds/{guild_id}/members/search?query={query}&limit={limit}",
                guild_id=guild_id,
                query=query,
                limit=limit,
            )
        )

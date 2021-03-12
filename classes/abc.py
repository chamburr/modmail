import discord

from classes.invite import Invite


class GuildChannel(discord.abc.GuildChannel):
    async def create_invite(self, *, reason=None, **fields):
        data = await self._state.http.create_invite(self.id, reason=reason, **fields)
        return await Invite.from_incomplete(data=data, state=self._state)

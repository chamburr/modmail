import logging

from discord import invite
from discord.enums import ChannelType, try_enum
from discord.invite import PartialInviteChannel, PartialInviteGuild

log = logging.getLogger(__name__)


class Invite(invite.Invite):
    @classmethod
    async def from_incomplete(cls, *, state, data):
        try:
            guild = await state._get_guild(int(data["guild"]["id"]))
            if guild is None:
                guild = PartialInviteGuild(state, data["guild"], int(data["guild"]["id"]))
        except KeyError:
            guild = None

        channel = PartialInviteChannel(
            id=int(data["channel"]["id"]),
            name=data["channel"]["name"],
            type=try_enum(ChannelType, data["channel"]["type"]),
        )

        if guild is not None and not isinstance(guild, PartialInviteGuild):
            channel = await guild.get_channel(int(data["channel"]["id"])) or channel

        data["guild"] = guild
        data["channel"] = channel

        return cls(state=state, data=data)

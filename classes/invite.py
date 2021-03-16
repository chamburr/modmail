import discord

from discord import PartialInviteChannel, PartialInviteGuild
from discord.enums import *


class Invite(discord.Invite):
    @classmethod
    async def from_incomplete(cls, *, state, data):
        try:
            guild_id = int(data["guild"]["id"])
        except KeyError:
            guild = None
        else:
            guild = await state._get_guild(guild_id)
            if guild is None:
                guild_data = data["guild"]
                guild = PartialInviteGuild(state, guild_data, guild_id)
        channel_data = data["channel"]
        channel_id = int(channel_data["id"])
        channel_type = try_enum(ChannelType, channel_data["type"])
        channel = PartialInviteChannel(id=channel_id, name=channel_data["name"], type=channel_type)
        if guild is not None and not isinstance(guild, PartialInviteGuild):
            channel = await guild.get_channel(channel_id) or channel

        data["guild"] = guild
        data["channel"] = channel
        return cls(state=state, data=data)

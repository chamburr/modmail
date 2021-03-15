import logging
import re

import dateparser
import discord

from discord.ext import commands
from discord.ext.commands import ChannelNotFound, MemberNotFound, NoPrivateMessage, RoleNotFound

from classes.channel import TextChannel
from classes.member import Member

log = logging.getLogger(__name__)


class ChannelConverter(commands.TextChannelConverter):
    async def convert(self, ctx, argument):
        bot = ctx.bot

        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        result = None
        guild = ctx.guild

        if match is None:
            for channel in await guild.text_channels():
                if channel.name == argument:
                    result = channel
                    break
        else:
            channel_id = int(match.group(1))
            if guild:
                result = await guild.get_channel(channel_id)
            else:
                result = await bot.get_channel(channel_id)

        if not isinstance(result, TextChannel):
            raise ChannelNotFound(argument)


class DateTimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        date = dateparser.parse(
            argument,
            settings={
                "DATE_ORDER": "DMY",
                "TIMEZONE": "UTC",
                "PREFER_DATES_FROM": "future",
                "RETURN_AS_TIMEZONE_AWARE": False,
            },
            languages=["en"],
        )
        if date is None:
            raise commands.BadArgument("Invalid date format")
        return date


class GuildConverter(commands.Converter):
    async def convert(self, ctx, argument):
        guild = await ctx.bot.get_guild(int(argument))
        if guild:
            return guild
        raise commands.BadArgument("Guild not found")


class MemberConverter(commands.MemberConverter):
    async def convert(self, ctx, argument):
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r"<@!?([0-9]+)>$", argument)
        guild = ctx.guild
        result = None

        if match is None:
            members = await bot.http.request_guild_members(guild.id, argument)
            if len(members) > 1:
                raise commands.BadArgument("Multiple users with the same username/nickname")
            result = Member(guild=guild, state=bot.state, data=members[0])
        else:
            if guild:
                result = await guild.fetch_member(int(match.group(1)))

        if result is None:
            raise MemberNotFound(argument)

        return result


class RoleConverter(commands.IDConverter):
    async def convert(self, ctx, argument):
        guild = ctx.guild
        if not guild:
            raise NoPrivateMessage()

        match = self._get_id_match(argument) or re.match(r"<@&([0-9]+)>$", argument)
        result = None
        if match:
            result = await guild.get_role(int(match.group(1)))

        if result is None:
            raise RoleNotFound(argument)
        return result


class PingRole(RoleConverter):
    async def convert(self, ctx, argument):
        try:
            return await super().convert(ctx, argument)
        except commands.BadArgument:
            return argument


class UserConverter(commands.UserConverter):
    async def convert(self, ctx, argument):
        match = self._get_id_match(argument) or re.match(r"<@!?([0-9]+)>$", argument)
        if match is not None:
            try:
                return await ctx.bot.fetch_user(int(match.group(1)))
            except discord.NotFound:
                pass
        raise commands.BadArgument("User not found")

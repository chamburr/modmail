import logging
import re

import dateparser
import discord

from discord.ext import commands
from discord.ext.commands.errors import (
    ChannelNotFound,
    GuildNotFound,
    MemberNotFound,
    NoPrivateMessage,
    RoleNotFound,
    UserNotFound,
)

from classes.channel import TextChannel
from classes.member import Member

log = logging.getLogger(__name__)


class ChannelConverter(commands.TextChannelConverter):
    async def convert(self, ctx, argument):
        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        if match:
            channel_id = int(match.group(1))
            channel = await ctx.bot.get_channel(channel_id)

            if isinstance(channel, TextChannel):
                return channel

        for channel in await ctx.guild.text_channels():
            if channel.name == argument:
                return channel

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
            raise commands.BadArgument("Invalid date format.")

        return date


class GuildConverter(commands.GuildConverter):
    async def convert(self, ctx, argument):
        try:
            guild = await ctx.bot.get_guild(int(argument))
            if guild:
                return guild
        except ValueError:
            pass

        raise GuildNotFound(argument)


class MemberConverter(commands.MemberConverter):
    async def convert(self, ctx, argument):
        match = self._get_id_match(argument) or re.match(r"<@!?([0-9]+)>$", argument)
        if match:
            try:
                return await ctx.guild.fetch_member(int(match.group(1)))
            except discord.NotFound:
                pass

        members = await ctx.bot.http.request_guild_members(ctx.guild.id, argument)
        if len(members) > 0:
            return Member(guild=ctx.guild, state=ctx.bot.state, data=members[0])

        raise MemberNotFound(argument)


class RoleConverter(commands.RoleConverter):
    async def convert(self, ctx, argument):
        if not ctx.guild:
            raise NoPrivateMessage()

        match = self._get_id_match(argument) or re.match(r"<@&([0-9]+)>$", argument)
        if match:
            role = await ctx.guild.get_role(int(match.group(1)))
            if role:
                return role

        for role in await ctx.guild.roles():
            if role.name == argument:
                return role

        raise RoleNotFound(argument)


class PingRoleConverter(RoleConverter):
    async def convert(self, ctx, argument):
        try:
            return await super().convert(ctx, argument)
        except commands.BadArgument:
            return argument


class UserConverter(commands.UserConverter):
    async def convert(self, ctx, argument):
        match = self._get_id_match(argument) or re.match(r"<@!?([0-9]+)>$", argument)
        if match:
            try:
                return await ctx.bot.fetch_user(int(match.group(1)))
            except discord.NotFound:
                pass

        raise UserNotFound(argument)

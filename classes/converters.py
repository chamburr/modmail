import logging
import re

import dateparser
import discord

from discord.ext import commands

log = logging.getLogger(__name__)


class DateTime(commands.Converter):
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


class PingRole(commands.RoleConverter):
    async def convert(self, ctx, argument):
        try:
            return await super().convert(ctx, argument)
        except commands.BadArgument:
            return argument


class GlobalUser(commands.UserConverter):
    async def convert(self, ctx, argument):
        try:
            return await super().convert(ctx, argument)
        except commands.BadArgument:
            pass
        match = self._get_id_match(argument) or re.match(r"<@!?([0-9]+)>$", argument)
        if match is not None:
            try:
                return await ctx.bot.fetch_user(int(match.group(1)))
            except discord.NotFound:
                pass
        raise commands.BadArgument("User not found")


class GlobalGuild(commands.Converter):
    async def convert(self, ctx, argument):
        guild = await ctx.bot.comm.handler("get_guild", -1, {"guild_id": int(argument)})
        if guild:
            return guild
        raise commands.BadArgument("Guild not found")

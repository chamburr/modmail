import logging
import re

import dateparser
import discord

from discord.ext import commands
from discord.ext.commands import RoleNotFound

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


class RoleConverter(commands.IDConverter):
    async def convert(self, ctx, argument):
        match = self._get_id_match(argument) or re.match(r"<@&([0-9]+)>$", argument)
        if match:
            result = await ctx.guild.get_role(int(match.group(1)))
        else:
            result = discord.utils.get(ctx.guild._roles.values(), name=argument)

        if result is None:
            raise RoleNotFound(argument)
        return result


class PingRole(RoleConverter):
    async def convert(self, ctx, argument):
        try:
            return await super().convert(ctx, argument)
        except commands.BadArgument:
            return argument


class GlobalUser(commands.UserConverter):
    async def convert(self, ctx, argument):
        match = self._get_id_match(argument) or re.match(r"<@!?([0-9]+)>$", argument)
        if match is not None:
            try:
                return await ctx.bot.fetch_user(int(match.group(1)))
            except discord.NotFound:
                pass
        raise commands.BadArgument("User not found")

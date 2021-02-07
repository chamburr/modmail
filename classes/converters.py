import logging

import dateparser

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

import asyncio
import logging
import sentry_sdk
from discord.ext import commands

import config
from classes.bot import ModMail
from utils.tools import get_guild_prefix

if config.testing is False:
    sentry_sdk.init(config.sentry_url)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)


def _get_guild_prefix(bot2, message):
    prefix = get_guild_prefix(bot2, message)
    return commands.when_mentioned_or(prefix)(bot2, message)


bot = ModMail(
    fetch_offline_members=True,
    command_prefix=_get_guild_prefix,
    case_insensitive=True,
    description="The one and only public ModMail Discord bot.",
    help_command=None,
    owner_id=config.owner,
    heartbeat_timeout=300,
)


@bot.event
async def on_message(_):
    pass


loop = asyncio.get_event_loop()
loop.run_until_complete(bot.start_bot())

import asyncio
import logging
import sys

import sentry_sdk

import config

from classes.bot import ModMail, when_mentioned_or
from utils.tools import get_guild_prefix

if config.testing is False:
    sentry_sdk.init(config.sentry_url)

if len(sys.argv) < 3:
    cluster_id = 1
    cluster_count = 1
else:
    cluster_id = int(sys.argv[1])
    cluster_count = int(sys.argv[2])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=f"discord-{cluster_id}.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

log = logging.getLogger(__name__)


def _get_guild_prefix(bot2, message):
    prefix = get_guild_prefix(bot2, message.guild)
    return when_mentioned_or(prefix)(bot2)


bot = ModMail(
    command_prefix=_get_guild_prefix,
    case_insensitive=True,
    help_command=None,
    cluster_id=cluster_id,
    cluster_count=cluster_count,
    version="2.1.1",
)


@bot.event
async def on_message(_):
    pass


loop = asyncio.get_event_loop()
loop.run_until_complete(bot.start())

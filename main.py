import asyncio
import logging
import sys

import sentry_sdk

import config

from classes.bot import ModMail
from utils import tools

if config.testing is False:
    sentry_sdk.init(config.sentry_url)

cluster_id = int(sys.argv[1])
cluster_count = int(sys.argv[2])
bot_id = int(sys.argv[3])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=f"logs/cluster-{cluster_id}.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

log = logging.getLogger(__name__)


async def command_prefix(bot2, message):
    prefix = await tools.get_guild_prefix(bot2, message.guild)
    return [f"<@{bot.id}> ", f"<@!{bot.id}> ", prefix]


bot = ModMail(
    command_prefix=command_prefix,
    bot_id=bot_id,
    cluster_id=cluster_id,
    cluster_count=cluster_count,
    version="3.0.0",
)


@bot.event
async def on_message(_):
    pass


loop = asyncio.get_event_loop()
loop.run_until_complete(bot.start())

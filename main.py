import asyncio
import json
import logging
import sys

import config
import discord
import sentry_sdk

from discord.ext import commands

from classes.bot import ModMail
from utils.tools import get_guild_prefix

if config.testing is False:
    sentry_sdk.init(config.sentry_url)

if len(sys.argv) < 5:
    shard_ids = [0]
    shard_count = 1
    cluster_id = 1
    cluster_count = 1
else:
    shard_ids = json.loads(sys.argv[1])
    shard_count = int(sys.argv[2])
    cluster_id = int(sys.argv[3])
    cluster_count = int(sys.argv[4])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=f"discord-{cluster_id}.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

log = logging.getLogger(__name__)


def _get_guild_prefix(bot2, message):
    prefix = get_guild_prefix(bot2, message.guild)
    return commands.when_mentioned_or(prefix)(bot2, message)


bot = ModMail(
    intents=discord.Intents(guilds=True, members=True, presences=True, messages=True, reactions=True),
    member_cache_flags=None,
    chunk_guilds_at_startup=config.fetch_all_members,
    command_prefix=_get_guild_prefix,
    case_insensitive=True,
    help_command=None,
    owner_id=config.owner,
    heartbeat_timeout=300,
    shard_ids=shard_ids,
    shard_count=shard_count,
    cluster_id=cluster_id,
    cluster_count=cluster_count,
    version="2.1.1",
)


@bot.event
async def on_message(_):
    pass


loop = asyncio.get_event_loop()
loop.run_until_complete(bot.start_bot())

import asyncio
import logging
import sqlite3
import sentry_sdk
from discord.ext import commands

import config
from classes.bot import ModMail
from utils.tools import get_guild_prefix

sentry_sdk.init("https://95aac4bfecc04935b60edfd375646919@sentry.io/1471399")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")
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
)

# bot.conn = sqlite3.connect('data.sqlite')
# c = bot.conn.cursor()
# c.execute("CREATE TABLE IF NOT EXISTS data "
#           "(guild bigint NOT NULL PRIMARY KEY, prefix text, category bigint, accessrole bigint, "
#           "logging bigint, welcome text, goodbye text, loggingplus integer, pingrole text)")
# c.execute("CREATE TABLE IF NOT EXISTS premium "
#           "(user bigint NOT NULL PRIMARY KEY, server text)")
# c.execute("CREATE TABLE IF NOT EXISTS banlist "
#           "(id bigint NOT NULL PRIMARY KEY, type text)")
# c.execute("CREATE TABLE IF NOT EXISTS usersettings "
#           "(user bigint NOT NULL PRIMARY KEY, confirmation int)")
# bot.conn.commit()


@bot.event
async def on_message(_):
    pass

loop = asyncio.get_event_loop()
loop.run_until_complete(bot.start_bot())

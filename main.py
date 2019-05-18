import asyncio
import logging
import sqlite3

import config
from classes.bot import ModMail
from utils.tools import get_guild_prefix


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)


bot = ModMail(
    fetch_offline_members=True,
    command_prefix=get_guild_prefix,
    case_insensitive=True,
    description="The one and only public ModMail Discord bot.",
    help_command=None,
    owner_id=config.owner,
)

# bot.conn = sqlite3.connect('data.sqlite')
# c = bot.conn.cursor()
# c.execute("CREATE TABLE IF NOT EXISTS data "
#           "(guild bigint NOT NULL PRIMARY KEY, prefix text, category bigint, accessrole bigint, "
#           "logging bigint, welcome text, goodbye text)")
# c.execute("CREATE TABLE IF NOT EXISTS premium "
#           "(user bigint NOT NULL PRIMARY KEY, server text)")
# bot.conn.commit()


@bot.event
async def on_message(_):
    pass

loop = asyncio.get_event_loop()
loop.run_until_complete(bot.start_bot())

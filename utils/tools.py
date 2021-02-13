import logging

from discord import utils

log = logging.getLogger(__name__)


def get_guild_prefix(bot, guild):
    if not guild:
        return bot.config.default_prefix
    guild_id = guild.id
    try:
        prefix = bot.all_prefix[guild_id]
        return bot.config.default_prefix if prefix is None else prefix
    except KeyError:
        return bot.config.default_prefix


async def get_user_premium(bot, user_id):
    guild = await bot.get_guild(bot.config.main_server)
    if not guild:
        return
    member = await bot._redis.sismember(f"guild_members:{guild.id}", user_id)
    if not member:
        return
    roles = (await bot.http.get_member(guild.id, user_id))["roles"]
    if user_id in bot.config.admins or user_id in bot.config.owners:
        amount = 1000
    elif bot.config.premium5 in roles:
        amount = 5
    elif bot.config.premium3 in roles:
        amount = 3
    elif bot.config.premium1 in roles:
        amount = 1
    else:
        amount = 0
    return amount


async def get_user_settings(bot, user):
    async with bot.pool.acquire() as conn:
        return await conn.fetchrow("SELECT identifier, confirmation FROM preference WHERE identifier=$1", user)


async def get_premium_slots(bot, user):
    if not bot.config.main_server:
        return False
    data = await get_user_premium(bot, user)
    if not data:
        async with bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT guild FROM premium WHERE identifier=$1", user)
            if res:
                return 1
        return False
    else:
        return data


async def wipe_premium(bot, user):
    async with bot.pool.acquire() as conn:
        res = await conn.fetchrow("SELECT identifier, guild FROM premium WHERE identifier=$1", user)
        if res:
            for guild in res[1]:
                await conn.execute(
                    "UPDATE data SET welcome=$1, goodbye=$2, loggingplus=$3 WHERE guild=$4",
                    None,
                    None,
                    False,
                    guild,
                )
                await conn.execute("DELETE FROM snippet WHERE guild=$1", guild)
        await conn.execute("DELETE FROM premium WHERE identifier=$1", user)


def get_modmail_user(channel):
    return int(channel.topic.replace("ModMail Channel ", "").split(" ")[0])


def perm_format(perm):
    return perm.replace("_", " ").replace("guild", "server").title()


def shorten_message(message):
    if len(message) > 2048:
        return message[:2045] + "..."
    else:
        return message


def tag_format(message, author):
    tags = {
        "{username}": author.name,
        "{usertag}": author.discriminator,
        "{userid}": str(author.id),
        "{usermention}": author.mention,
    }
    for tag, val in tags.items():
        message = message.replace(tag, val)
    return shorten_message(message)

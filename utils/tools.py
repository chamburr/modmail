import logging

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


async def get_user_settings(bot, user):
    async with bot.pool.acquire() as conn:
        return await conn.fetchrow("SELECT identifier, confirmation FROM preference WHERE identifier=$1", user)


async def get_premium_slots(bot, user):
    if not bot.config.main_server:
        return False
    data = await bot.comm.handler("get_user_premium", -1, {"user_id": user})
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

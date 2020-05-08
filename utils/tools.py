import logging

log = logging.getLogger(__name__)


def get_guild_prefix(bot, guild, json_dict=False):
    if not guild:
        return bot.config.default_prefix
    if json_dict:
        guild_id = guild["id"]
    else:
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
    data = await bot.cogs["Communication"].handler("get_user_premium", 1, {"user_id": user})
    if not data or data[0] == 0:
        return False
    else:
        return data[0]


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

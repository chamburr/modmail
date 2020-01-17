import discord.utils as utils


def get_guild_prefix(bot, message):
    if not message.guild:
        return bot.config.default_prefix
    try:
        prefix = bot.all_prefix[message.guild.id]
        return bot.config.default_prefix if prefix is None else prefix
    except KeyError:
        c = bot.conn.cursor()
        c.execute("SELECT prefix FROM data WHERE guild=?", (message.guild.id,))
        prefix = c.fetchone()
        if prefix and prefix[0]:
            bot.all_prefix[message.guild.id] = prefix[0]
            return prefix[0]
        else:
            bot.all_prefix[message.guild.id] = None
            return bot.config.default_prefix


def get_user_settings(bot, user):
    c = bot.conn.cursor()
    c.execute("SELECT * FROM usersettings WHERE user=?", (user,))
    res = c.fetchone()
    return res


def get_premium_slots(bot, user):
    guild = bot.get_guild(bot.config.main_server)
    member = guild.get_member(user)
    if not member:
        return False
    elif user in bot.config.admins or user in bot.config.owners:
        return 1000
    elif utils.get(member.roles, id=bot.config.premium5):
        return 5
    elif utils.get(member.roles, id=bot.config.premium3):
        return 3
    elif utils.get(member.roles, id=bot.config.premium1):
        return 1
    else:
        return False


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

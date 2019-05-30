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
        if prefix is not None and prefix[0] is not None:
            bot.all_prefix[message.guild.id] = prefix[0]
            return prefix[0]
        else:
            bot.all_prefix[message.guild.id] = None
            return bot.config.default_prefix


def get_premium_slots(bot, user):
    guild = bot.get_guild(bot.config.main_server)
    member = guild.get_member(user)
    if not member:
        return False
    elif user in bot.config.admins or user in bot.config.owners:
        return 1000
    elif utils.get(member.roles, id=bot.config.premium_advanced) is not None:
        return 10
    elif utils.get(member.roles, id=bot.config.premium_plus) is not None:
        return 5
    elif utils.get(member.roles, id=bot.config.premium) is not None:
        return 2
    else:
        return False


def perm_format(perm):
    return perm.replace('_', ' ').replace('guild', 'server').title()

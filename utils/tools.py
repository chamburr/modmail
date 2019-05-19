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

async def get_premium_slots(self, user):
    guild = self.bot.get_guild(self.bot.config.main_server)
    member = guild.get_member(user)
    if not member:
        return False
    elif utils.get(member.roles, id=self.bot.config.premium_advanced) is not None:
        return 10
    elif utils.get(member.roles, id=self.bot.config.premium_plus) is not None:
        return 5
    elif utils.get(member.roles, id=self.bot.config.premium) is not None:
        return 2
    else:
        return False

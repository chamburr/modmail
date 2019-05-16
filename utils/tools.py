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

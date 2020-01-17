import discord
from discord.ext import commands


def is_owner():
    def predicate(ctx):
        if ctx.author.id not in ctx.bot.config.owners:
            raise commands.NotOwner()
        else:
            return True

    return commands.check(predicate)


def is_admin():
    def predicate(ctx):
        if ctx.author.id not in ctx.bot.config.admins and ctx.author.id not in ctx.bot.config.owners:
            raise commands.NotOwner()
        else:
            return True

    return commands.check(predicate)


def in_database():
    async def predicate(ctx):
        c = ctx.bot.conn.cursor()
        c.execute("SELECT * FROM data WHERE guild=?", (ctx.guild.id,))
        res = c.fetchone()
        if res is None or res[2] is None:
            await ctx.send(
                embed=discord.Embed(
                    description=f"Your server has not been set up yet. Use `{ctx.prefix}setup` first.",
                    colour=ctx.bot.error_colour,
                )
            )
        return True if res else False

    return commands.check(predicate)


def is_premium():
    async def predicate(ctx):
        c = ctx.bot.conn.cursor()
        c.execute("SELECT server FROM premium")
        res = c.fetchall()
        all_premium = []
        for row in res:
            if row[0] is None:
                continue
            row = row[0].split(",")
            for guild in row:
                all_premium.append(guild)
        if str(ctx.guild.id) not in all_premium:
            await ctx.send(
                embed=discord.Embed(
                    description="This server does not have premium. Want to get premium? More information "
                    f"is available with the `{ctx.prefix}premium` command.",
                    colour=ctx.bot.error_colour,
                )
            )
            return False
        else:
            return True

    return commands.check(predicate)


def is_patron():
    async def predicate(ctx):
        c = ctx.bot.conn.cursor()
        c.execute("SELECT user FROM premium WHERE user=?", (ctx.author.id,))
        res = c.fetchone()
        if res is None:
            slots = ctx.bot.tools.get_premium_slots(ctx.bot, ctx.author.id)
            if slots is False:
                await ctx.send(
                    embed=discord.Embed(
                        description="This command requires you to be a patron. Want to become a patron? More "
                        f"information is available with the `{ctx.prefix}premium` command.",
                        colour=ctx.bot.error_colour,
                    )
                )
                return False
            else:
                c.execute(
                    "INSERT INTO premium (user, server) VALUES (?, ?)", (ctx.author.id, None),
                )
                ctx.bot.conn.commit()
                return True
        else:
            return True

    return commands.check(predicate)


def is_modmail_channel2(bot, channel, user_id=None):
    return (
        channel.category_id
        and channel.category_id in bot.all_category
        and channel.topic
        and channel.topic.startswith("ModMail Channel ")
        and channel.topic.replace("ModMail Channel ", "").split(" ")[0].isdigit()
        and (channel.topic.replace("ModMail Channel ", "").split(" ")[0] == str(user_id) if user_id else True)
    )


def is_modmail_channel():
    async def predicate(ctx):
        if not is_modmail_channel2(ctx.bot, ctx.channel):
            await ctx.send(
                embed=discord.Embed(description="This channel is not a ModMail channel.", colour=ctx.bot.error_colour)
            )
            return False
        else:
            return True

    return commands.check(predicate)


def is_mod():
    async def predicate(ctx):
        has_role = False
        roles = ctx.bot.get_data(ctx.guild.id)[3]
        if roles:
            for role in roles.split(","):
                role = ctx.guild.get_role(int(role))
                if role is None:
                    continue
                if role in ctx.author.roles:
                    has_role = True
                    break
        if has_role is False and ctx.author.guild_permissions.administrator is False:
            await ctx.send(
                embed=discord.Embed(
                    description=f"You do not have access to use this command.", colour=ctx.bot.error_colour,
                )
            )
            return False
        else:
            return True

    return commands.check(predicate)

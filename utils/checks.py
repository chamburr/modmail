import logging

import discord

from discord.ext import commands
from discord.ext.commands import BotMissingPermissions, MissingPermissions

from classes.state import PartialChannel

log = logging.getLogger(__name__)


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
        async with ctx.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT category FROM data WHERE guild=$1", ctx.guild.id)
        if not res or not res[0]:
            await ctx.send(
                embed=discord.Embed(
                    description=f"Your server has not been set up yet. Use `{ctx.prefix}setup` first.",
                    colour=ctx.bot.error_colour,
                )
            )
        return True if res and res[0] else False

    return commands.check(predicate)


def is_premium():
    async def predicate(ctx):
        if not ctx.bot.config.main_server:
            return True
        async with ctx.bot.pool.acquire() as conn:
            res = await conn.fetch("SELECT guild FROM premium")
        all_premium = []
        for row in res:
            all_premium.extend(row[0])
        if ctx.guild.id not in all_premium:
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
        async with ctx.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT identifier FROM premium WHERE identifier=$1", ctx.author.id)
        if res:
            return True
        slots = await ctx.bot.tools.get_premium_slots(ctx.bot, ctx.author.id)
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
            async with ctx.bot.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO premium (identifier, guild) VALUES ($1, $2)",
                    ctx.author.id,
                    [],
                )
            return True

    return commands.check(predicate)


def is_modmail_channel2(bot, channel, user_id=None):
    return (
        channel.topic
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
        roles = (await ctx.bot.get_data(ctx.guild.id))[3]
        for role in roles:
            role = await ctx.guild.get_role(role)
            if not role:
                continue
            if role in (await ctx.message.member())._roles:
                return True
        if (await ctx.message.member()).guild_permissions.administrator is False and has_role is False:
            await ctx.send(
                embed=discord.Embed(
                    description="You do not have access to use this command.",
                    colour=ctx.bot.error_colour,
                )
            )
            return False
        else:
            return True

    return commands.check(predicate)


def has_permissions(**perms):
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    async def predicate(ctx):
        permissions = await ctx.channel.permissions_for(ctx.message.member)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise MissingPermissions(missing)

    return commands.check(predicate)


def bot_has_permissions(**perms):
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    async def predicate(ctx):
        if isinstance(ctx.channel, PartialChannel):
            return True

        permissions = await ctx.channel.permissions_for(await ctx.guild.me())

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise BotMissingPermissions(missing)

    return commands.check(predicate)

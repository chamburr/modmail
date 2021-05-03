import logging

from discord.ext import commands
from discord.ext.commands import BotMissingPermissions, MissingPermissions

from classes.channel import TextChannel
from classes.embed import ErrorEmbed
from utils import tools

log = logging.getLogger(__name__)


def is_owner():
    def predicate(ctx):
        if ctx.author.id not in ctx.bot.config.owners:
            raise commands.NotOwner()

        return True

    return commands.check(predicate)


def is_admin():
    def predicate(ctx):
        if ctx.author.id not in ctx.bot.config.owners + ctx.bot.config.admins:
            raise commands.NotOwner()

        return True

    return commands.check(predicate)


def in_database():
    async def predicate(ctx):
        async with ctx.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT category FROM data WHERE guild=$1", ctx.guild.id)

        if not res or not res[0]:
            await ctx.send(
                embed=ErrorEmbed(
                    description=f"Your server has not been set up yet. Use `{ctx.prefix}setup` first."
                )
            )
            return False

        return True

    return commands.check(predicate)


def is_premium():
    async def predicate(ctx):
        if not ctx.bot.config.main_server:
            return True

        async with ctx.bot.pool.acquire() as conn:
            res = await conn.fetchrow(
                "SELECT identifier FROM premium WHERE $1=any(guild)", ctx.guild.id
            )

        if not res:
            await ctx.send(
                embed=ErrorEmbed(
                    description="This server does not have premium. Want to get premium? More information is available "
                    f"with the `{ctx.prefix}premium` command."
                )
            )
            return False

        return True

    return commands.check(predicate)


def is_patron():
    async def predicate(ctx):
        async with ctx.bot.pool.acquire() as conn:
            res = await conn.fetchrow(
                "SELECT identifier FROM premium WHERE identifier=$1", ctx.author.id
            )

        if res:
            return True

        if await tools.get_premium_slots(ctx.bot, ctx.author.id) is False:
            await ctx.send(
                embed=ErrorEmbed(
                    description="This command requires you to be a patron. Want to become a patron? More information "
                    f"is available with the `{ctx.prefix}premium` command."
                )
            )
            return False

        async with ctx.bot.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO premium (identifier, guild) VALUES ($1, $2)", ctx.author.id, []
            )

        return True

    return commands.check(predicate)


def is_modmail_channel():
    async def predicate(ctx):
        if not tools.is_modmail_channel(ctx.channel):
            await ctx.send(embed=ErrorEmbed(description="This channel is not a ModMail channel."))
            return False

        return True

    return commands.check(predicate)


def is_mod():
    async def predicate(ctx):
        if (await ctx.message.member.guild_permissions()).administrator:
            return True

        for role in (await tools.get_data(ctx.bot, ctx.guild.id))[3]:
            if role in ctx.message.member._roles:
                return True

        await ctx.send(embed=ErrorEmbed(description="You do not have access to this command."))
        return False

    return commands.check(predicate)


def has_permissions(**perms):
    async def predicate(ctx):
        permissions = await ctx.channel.permissions_for(ctx.message.member)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise MissingPermissions(missing)

    return commands.check(predicate)


def bot_has_permissions(**perms):
    async def predicate(ctx):
        if not isinstance(ctx.channel, TextChannel):
            return True

        permissions = await ctx.channel.permissions_for(await ctx.guild.me())
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise BotMissingPermissions(missing)

    return commands.check(predicate)

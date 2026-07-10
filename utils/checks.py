from __future__ import annotations

import logging

from typing import TYPE_CHECKING

from discord.ext import commands
from discord.ext.commands import BotMissingPermissions, MissingPermissions

from classes.channel import TextChannel
from classes.embed import ErrorEmbed
from utils import tools

if TYPE_CHECKING:
    from discord.ext.commands._types import Check

    from classes.context import Context

log = logging.getLogger(__name__)


def is_owner() -> Check[Context]:
    def predicate(ctx: Context) -> bool:
        if str(ctx.author.id) not in (ctx.bot.config.OWNER_USERS or "").split(","):
            raise commands.NotOwner()

        return True

    return commands.check(predicate)


def is_admin() -> Check[Context]:
    def predicate(ctx: Context) -> bool:
        if str(ctx.author.id) not in (
            (ctx.bot.config.OWNER_USERS or "").split(",")
            + (ctx.bot.config.ADMIN_USERS or "").split(",")
        ):
            raise commands.NotOwner()

        return True

    return commands.check(predicate)


def in_database() -> Check[Context]:
    async def predicate(ctx: Context) -> bool:
        async with ctx.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT category FROM data WHERE guild=$1", ctx.guild.id)

        if not res or not res[0]:
            await ctx.send(
                ErrorEmbed(f"Your server has not been set up yet. Use `{ctx.prefix}setup` first.")
            )
            return False

        return True

    return commands.check(predicate)


def is_premium() -> Check[Context]:
    async def predicate(ctx: Context) -> bool:
        if not ctx.bot.config.MAIN_SERVER:
            return True

        async with ctx.bot.pool.acquire() as conn:
            res = await conn.fetchrow(
                "SELECT identifier FROM premium WHERE $1=any(guild)", ctx.guild.id
            )

        if not res:
            await ctx.send(
                ErrorEmbed(
                    "This server does not have premium. Want to get premium? More information is "
                    f"available with the `{ctx.prefix}premium` command."
                )
            )
            return False

        return True

    return commands.check(predicate)


def is_patron() -> Check[Context]:
    async def predicate(ctx: Context) -> bool:
        async with ctx.bot.pool.acquire() as conn:
            res = await conn.fetchrow(
                "SELECT identifier FROM premium WHERE identifier=$1", ctx.author.id
            )

        if res:
            return True

        if await tools.get_premium_slots(ctx.bot, ctx.author.id) == 0:
            await ctx.send(
                ErrorEmbed(
                    "This command requires you to be a patron. Want to become a patron? More "
                    f"information is available with the `{ctx.prefix}premium` command."
                )
            )
            return False

        async with ctx.bot.pool.acquire() as conn:
            await conn.execute("INSERT INTO premium VALUES ($1, $2, NULL)", ctx.author.id, [])

        return True

    return commands.check(predicate)


def is_modmail_channel() -> Check[Context]:
    async def predicate(ctx: Context) -> bool:
        if not tools.is_modmail_channel(ctx.channel):
            await ctx.send(ErrorEmbed("This channel is not a ModMail channel."))
            return False

        return True

    return commands.check(predicate)


def is_mod() -> Check[Context]:
    async def predicate(ctx: Context) -> bool:
        if (await ctx.message.member.guild_permissions()).administrator:
            return True

        for role in (await tools.get_data(ctx.bot, ctx.guild.id))[3]:
            if role in ctx.message.member._roles:
                return True

        await ctx.send(ErrorEmbed("You do not have access to this command."))
        return False

    return commands.check(predicate)


def has_permissions(**perms: bool) -> Check[Context]:
    async def predicate(ctx: Context) -> bool:
        permissions = await ctx.channel.permissions_for(ctx.message.member)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise MissingPermissions(missing)

    return commands.check(predicate)


def bot_has_permissions(**perms: bool) -> Check[Context]:
    async def predicate(ctx: Context) -> bool:
        if not isinstance(ctx.channel, TextChannel):
            return True

        permissions = await ctx.channel.permissions_for(await ctx.guild.me())
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise BotMissingPermissions(missing)

    return commands.check(predicate)

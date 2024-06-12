import logging
import traceback

import discord

from discord.ext import commands

from classes.embed import ErrorEmbed
from utils import tools

log = logging.getLogger(__name__)


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.on_command_error = self._on_command_error

    async def _on_command_error(self, ctx, error, bypass=False):
        if (
            hasattr(ctx.command, "on_error")
            or (ctx.command and hasattr(ctx.cog, f"_{ctx.command.cog_name}__error"))
            and not bypass
        ):
            return

        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                ErrorEmbed("Command Unavailable", "This command cannot be used in direct message.")
            )
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(
                ErrorEmbed(
                    "Command Unavailable",
                    "This command can only be used in direct message.",
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument) or isinstance(
            error, commands.BadArgument
        ):
            embed = ErrorEmbed(
                "Invalid Arguments",
                "Please check the usage below or join the support server with "
                f"`{ctx.prefix}support` if you don't know what went wrong.",
            )
            usage = "\n".join([ctx.prefix + x.strip() for x in ctx.command.usage.split("\n")])
            embed.add_field("Usage", f"```{usage}```")
            await ctx.send(embed)
        elif isinstance(error, commands.NotOwner):
            await ctx.send(
                ErrorEmbed("Permission Denied", "You do not have permission to use this command.")
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                ErrorEmbed(
                    "Permission Denied",
                    "You do not have permission to use this command. Permissions needed: "
                    f"{', '.join([tools.perm_format(x) for x in error.missing_perms])}.",
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                ErrorEmbed(
                    "Bot Missing Permissions",
                    "Bot is missing permissions to perform that action. Permissions needed: "
                    f"{', '.join([tools.perm_format(x) for x in error.missing_perms])}.",
                )
            )
        elif isinstance(error, discord.HTTPException):
            await ctx.send(
                ErrorEmbed(
                    "Unknown HTTP Exception",
                    f"Please report this in the support server.\n```{error.text}````",
                )
            )
        elif isinstance(error, commands.CommandInvokeError):
            log.error(
                f"{error.original.__class__.__name__}: {error.original} (In {ctx.command.name})\n"
                f"Traceback:\n{''.join(traceback.format_tb(error.original.__traceback__))}"
            )

            try:
                await ctx.send(
                    ErrorEmbed(
                        "Unknown Error",
                        "Please report this in the support server.\n"
                        f"```{error.original.__class__.__name__}: {error.original}```",
                    )
                )
            except discord.HTTPException:
                pass


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))

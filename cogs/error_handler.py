import discord
import logging
import traceback
import sys
from discord.ext import commands

from utils.tools import perm_format

log = logging.getLogger(__name__)


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.on_command_error = self._on_command_error
        self.client = None

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
                embed=discord.Embed(
                    title="Command Unavailable",
                    description="This command cannot be used in Direct Message.",
                    colour=self.bot.error_colour,
                )
            )
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(
                embed=discord.Embed(
                    title="Command Unavailable",
                    description="This command can only be used in Direct Message.",
                    colour=self.bot.error_colour,
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Invalid Arguments",
                description=f"Please check the usage below or join the support server with "
                f"`{ctx.prefix}support` if you don't know what went wrong.",
                colour=self.bot.error_colour,
            )
            usage = "\n".join([ctx.prefix + x.strip() for x in ctx.command.usage.split("\n")])
            embed.add_field(name="Usage", value=f"```{usage}```")
            await ctx.send(embed=embed)
        elif isinstance(error, commands.NotOwner):
            await ctx.send(
                embed=discord.Embed(
                    title="Permission Denied",
                    description="You do not have permission to use this command.",
                    colour=self.bot.error_colour,
                )
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=discord.Embed(
                    title="Permission Denied",
                    description="You do not have permission to use this command. "
                    f"Permissions needed: {', '.join([perm_format(p) for p in error.missing_perms])}",
                    colour=self.bot.error_colour,
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=discord.Embed(
                    title="Bot Missing Permissions",
                    description="Bot is missing permissions to perform that action. The following permissions are"
                    f" needed: {', '.join([perm_format(p) for p in error.missing_perms])}",
                    colour=self.bot.error_colour,
                )
            )
        elif isinstance(error, discord.HTTPException):
            await ctx.send(
                embed=discord.Embed(
                    title="Unknown HTTP Exception",
                    description=f"Please report this in the support server.\n```{error.text}````",
                    colour=self.bot.error_colour,
                )
            )
        elif isinstance(error, commands.CommandInvokeError):
            log.error(
                f"{error.original.__class__.__name__}: {error.original} (In {ctx.command.name})\n"
                f"Traceback:\n{traceback.print_tb(error.original.__traceback__)}"
            )
            await ctx.send(
                embed=discord.Embed(
                    title="Unknown Error",
                    description=f"Please report this in the support server.\n```{error.original.__class__.__name__}: "
                    f"{error.original}```",
                    colour=self.bot.error_colour,
                )
            )


def setup(bot):
    bot.add_cog(ErrorHandler(bot))

import discord
import traceback
import sys
from discord.ext import commands

from utils.tools import perm_format


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.on_command_error = self._on_command_error
        self.client = None

    async def _on_command_error(self, ctx, error, bypass=False):
        if hasattr(ctx.command, "on_error") or (ctx.command and hasattr(ctx.cog, f"_{ctx.command.cog_name}__error")) \
           and not bypass:
            return
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                embed=discord.Embed(
                    title="Command Unavailable",
                    description="This command cannot be used in Direct Message.",
                    color=self.bot.error_colour,
                )
            )
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(
                embed=discord.Embed(
                    title="Command Unavailable",
                    description="This command can only be used in Direct Message.",
                    color=self.bot.error_colour,
                )
            )
        elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(
                    title="Invalid Arguments",
                    description=f"Please try using `{ctx.prefix}help` or join the support server with "
                                f"`{ctx.prefix}support` if you don't know what went wrong.",
                    color=self.bot.error_colour,
                )
            )
        elif isinstance(error, commands.NotOwner):
            await ctx.send(
                embed=discord.Embed(
                    title="Permission Denied",
                    description="You do not have permission to use this command.",
                    color=self.bot.error_colour,
                )
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=discord.Embed(
                    title="Permission Denied",
                    description="You do not have permission to use this command. "
                                f"Permissions needed: {', '.join([perm_format(p) for p in error.missing_perms])}",
                    color=self.bot.error_colour,
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=discord.Embed(
                    title="Bot Missing Permissions",
                    description="Bot is missing permissions to perform that action. The following permissions are"
                                f" needed: {', '.join([perm_format(p) for p in error.missing_perms])}",
                    color=self.bot.error_colour,
                )
            )
        elif isinstance(error, discord.HTTPException):
            await ctx.send(
                embed=discord.Embed(
                    title="Unknown Error",
                    description=f"```{error.text}````",
                    color=self.bot.error_colour,
                )
            )
        elif isinstance(error, commands.CommandInvokeError):
            print("In {}:".format(ctx.command.name), file=sys.stderr)
            traceback.print_tb(error.original.__traceback__)
            print("{0}: {1}".format(error.original.__class__.__name__, error.original), file=sys.stderr)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))

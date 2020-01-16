import copy
import discord
import logging
import traceback
import textwrap
import io
import subprocess

from typing import Optional
from contextlib import redirect_stdout
from importlib import reload as importlib_reload
from discord.ext import commands

from utils import checks

log = logging.getLogger(__name__)


def cleanup_code(content):
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])
        return content.strip("` \n")


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    @checks.is_owner()
    @commands.command(description="Load a module.", usage="load <cog>", hidden=True)
    async def load(self, ctx, *, cog: str):
        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(description=f"ERROR: {type(e).__name__} - {e}", colour=self.bot.error_colour)
            )
        else:
            await ctx.send(
                embed=discord.Embed(description="Successfully loaded the module.", colour=self.bot.primary_colour)
            )

    @checks.is_owner()
    @commands.command(description="Unload a module.", usage="unload <cog>", hidden=True)
    async def unload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(description=f"ERROR: {type(e).__name__} - {e}", colour=self.bot.error_colour)
            )
        else:
            await ctx.send(
                embed=discord.Embed(description="Successfully unloaded the module.", colour=self.bot.primary_colour)
            )

    @checks.is_owner()
    @commands.command(description="Reload a module.", usage="reload <cog>", hidden=True)
    async def reload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(description=f"ERROR: {type(e).__name__} - {e}", colour=self.bot.error_colour)
            )
        else:
            await ctx.send(
                embed=discord.Embed(description="Successfully reloaded the module.", colour=self.bot.primary_colour)
            )

    @checks.is_owner()
    @commands.command(description="Reload the configurations.", usage="reloadconf", hidden=True)
    async def reloadconf(self, ctx):
        try:
            importlib_reload(self.bot.config)
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(description=f"ERROR: {type(e).__name__} - {e}", colour=self.bot.error_colour)
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully reloaded the configurations.", colour=self.bot.primary_colour,
                )
            )

    @commands.is_owner()
    @commands.command(description="Restart the bot.", usage="restart", hidden=True)
    async def restart(self, ctx):
        await ctx.send(embed=discord.Embed(description="Restarting...", colour=self.bot.primary_colour))
        await self.bot.logout()

    @checks.is_owner()
    @commands.command(name="eval", description="Evaluate code", usage="eval <code>", hidden=True)
    async def _eval(self, ctx, *, body: str):
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "_": self._last_result,
        }
        env.update(globals())
        body = cleanup_code(body)
        stdout = io.StringIO()
        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'
        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"```py\n{e.__class__.__name__}: {e}\n```", colour=self.bot.primary_colour,
                )
            )
        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(
                embed=discord.Embed(
                    description=f"```py\n{value}{traceback.format_exc()}\n```", colour=self.bot.error_colour,
                )
            )
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction("✅")
            except discord.Forbidden:
                pass
            if ret is None:
                if value:
                    await ctx.send(
                        embed=discord.Embed(descrption=f"```py\n{value}\n```", colour=self.bot.primary_colour)
                    )
            else:
                self._last_result = ret
                await ctx.send(
                    embed=discord.Embed(description=f"```py\n{value}{ret}\n```", colour=self.bot.primary_colour)
                )

    @checks.is_owner()
    @commands.command(description="Execute code in bash.", usage="bash <command>", hidden=True)
    async def bash(self, ctx, *, command_to_run: str):
        try:
            output = subprocess.check_output(command_to_run.split(), stderr=subprocess.STDOUT).decode("utf-8")
            await ctx.send(embed=discord.Embed(description=f"```py\n{output}\n```", colour=self.bot.primary_colour))
        except Exception as error:
            await ctx.send(
                embed=discord.Embed(
                    description=f"```py\n{error.__class__.__name__}: {error}\n```", colour=self.bot.error_colour,
                )
            )

    @checks.is_owner()
    @commands.command(description="Execute SQL.", usage="sql <query>", hidden=True)
    async def sql(self, ctx, *, query: str):
        c = self.bot.conn.cursor()
        try:
            c.execute(query)
            res = c.fetchone()
            self.bot.conn.commit()
        except Exception:
            return await ctx.send(
                embed=discord.Embed(description=f"```py\n{traceback.format_exc()}```", colour=self.bot.error_colour)
            )
        if res:
            await ctx.send(embed=discord.Embed(description=f"```{res}```", colour=self.bot.primary_colour))
        else:
            await ctx.send(embed=discord.Embed(description="No results to fetch.", colour=self.bot.primary_colour))

    @checks.is_owner()
    @commands.command(
        description="Get the bot logs. Default to 10 lines.", usage="botlogs [lines]", hideen=True,
    )
    async def botlogs(self, ctx, *, lines: int = 10):
        with open("discord.log", "r") as file:
            content = file.readlines()
        if lines > len(content):
            lines = len(content)
        content = "\n".join(content[(len(content) - lines) :])
        try:
            await ctx.send(embed=discord.Embed(description=f"```{content}```", colour=self.bot.primary_colour))
        except discord.HTTPException:
            await ctx.send(
                embed=discord.Embed(description="The message is too long to be sent.", colour=self.bot.error_colour)
            )

    @checks.is_owner()
    @commands.command(
        description="Invoke the command as another user and optionally in another channel.",
        usage="invoke [channel] <user> <command>",
        hidden=True,
    )
    async def invoke(self, ctx, channel: Optional[discord.TextChannel], user: discord.User, *, command: str):
        msg = copy.copy(ctx.message)
        channel = channel or ctx.channel
        msg.channel = channel
        msg.author = channel.guild.get_member(user.id) or user
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @checks.is_owner()
    @commands.command(
        description="Remove a user's premium.", usage="wipepremium <user>", hidden=True,
    )
    async def wipepremium(self, ctx, *, user: discord.User):
        c = self.bot.conn.cursor()
        c.execute("SELECT * FROM premium WHERE user=?", (user.id,))
        res = c.fetchone()
        for guild in res[1].split(","):
            c.execute("UPDATE data SET welcome=?, goodbye=?, loggingplus=? WHERE guild=?", (None, None, None, guild))
            self.bot.conn.commit()
        c.execute("DELETE FROM premium WHERE user=?", (user.id,))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(
                description="Successfully removed that user's premium.", colour=self.bot.primary_colour,
            )
        )

    @checks.is_owner()
    @commands.command(
        description="Make me say something.", usage="echo <message>", rest_is_raw=True, hidden=True,
    )
    async def echo(self, ctx, *, content):
        await ctx.send(content)

    @checks.is_owner()
    @commands.command(description="Ban a user from the bot", usage="banuser <user>", hidden=True)
    async def banuser(self, ctx, *, user: discord.User):
        c = self.bot.conn.cursor()
        c.execute("SELECT * FROM banlist WHERE id=? AND type=?", (user.id, "user"))
        res = c.fetchone()
        if not res:
            c.execute("INSERT INTO banlist (id, type) VALUES (?, ?)", (user.id, "user"))
            self.bot.conn.commit()
            self.bot.banned_users.append(user.id)
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully banned that user from the bot.", colour=self.bot.primary_colour,
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(description="That user is already banned.", colour=self.bot.error_colour)
            )

    @checks.is_owner()
    @commands.command(description="Unban a user from the bot", usage="unbanuser <user>", hidden=True)
    async def unbanuser(self, ctx, *, user: discord.User):
        c = self.bot.conn.cursor()
        c.execute("SELECT * FROM banlist WHERE id=? AND type=?", (user.id, "user"))
        res = c.fetchone()
        if res:
            c.execute("DELETE FROM banlist WHERE id=? AND type=?", (user.id, "user"))
            self.bot.conn.commit()
            self.bot.banned_users.remove(user.id)
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully unbanned that user from the bot.", colour=self.bot.primary_colour,
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(description="That user is not already banned.", colour=self.bot.error_colour)
            )

    @checks.is_owner()
    @commands.command(
        description="Make the bot leave a server.", usage="leaveserver <server ID>", hidden=True,
    )
    async def leaveserver(self, ctx, *, guild: int):
        guild = self.bot.get_guild(guild)
        if not guild:
            return await ctx.send(
                embed=discord.Embed(description="That server is not found", colour=self.bot.error_colour)
            )
        else:
            await guild.leave()
            await ctx.send(
                embed=discord.Embed(description="The bot has left that server.", colour=self.bot.primary_colour)
            )

    @checks.is_owner()
    @commands.command(
        description="Ban a server from the bot", usage="banserver <server ID>", hidden=True,
    )
    async def banserver(self, ctx, *, guild: int):
        if not self.bot.get_guild(guild):
            return await ctx.send(
                embed=discord.Embed(description="That server is not found", colour=self.bot.error_colour)
            )
        c = self.bot.conn.cursor()
        c.execute("SELECT * FROM banlist WHERE id=? AND type=?", (guild, "guild"))
        res = c.fetchone()
        if not res:
            c.execute("INSERT INTO banlist (id, type) VALUES (?, ?)", (guild, "guild"))
            self.bot.conn.commit()
            self.bot.banned_guilds.append(guild)
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully banned that server from the bot.", colour=self.bot.primary_colour,
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(description="That server is already banned.", colour=self.bot.error_colour)
            )

    @checks.is_owner()
    @commands.command(
        description="Unban a server from the bot", usage="unbanserver <server ID>", hidden=True,
    )
    async def unbanserver(self, ctx, *, guild: int):
        c = self.bot.conn.cursor()
        c.execute("SELECT * FROM banlist WHERE id=? AND type=?", (guild, "guild"))
        res = c.fetchone()
        if res:
            c.execute("DELETE FROM banlist WHERE id=? AND type=?", (guild, "guild"))
            self.bot.conn.commit()
            self.bot.banned_guilds.remove(guild)
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully unbanned that server from the bot.", colour=self.bot.primary_colour,
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(description="That server is not already banned.", colour=self.bot.error_colour)
            )


def setup(bot):
    bot.add_cog(Owner(bot))

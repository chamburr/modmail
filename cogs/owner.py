import copy
import io
import logging
import subprocess
import textwrap
import traceback

from contextlib import redirect_stdout
from datetime import timezone
from typing import Optional

import discord

from discord.ext import commands

from classes import converters
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
        data = await self.bot.comm.handler("load_extension", self.bot.cluster_count, {"cog": cog})
        if not data or data[0] != "Success":
            await ctx.send(embed=discord.Embed(description=f"Error: {data[0]}", colour=self.bot.error_colour))
        else:
            await ctx.send(
                embed=discord.Embed(description="Successfully loaded the module.", colour=self.bot.primary_colour)
            )

    @checks.is_owner()
    @commands.command(description="Unload a module.", usage="unload <cog>", hidden=True)
    async def unload(self, ctx, *, cog: str):
        data = await self.bot.comm.handler("unload_extension", self.bot.cluster_count, {"cog": cog})
        if not data or data[0] != "Success":
            await ctx.send(embed=discord.Embed(description=f"Error: {data[0]}", colour=self.bot.error_colour))
        else:
            await ctx.send(
                embed=discord.Embed(description="Successfully unloaded the module.", colour=self.bot.primary_colour)
            )

    @checks.is_owner()
    @commands.command(description="Reload a module.", usage="reload <cog>", hidden=True)
    async def reload(self, ctx, *, cog: str):
        data = await self.bot.comm.handler("reload_extension", self.bot.cluster_count, {"cog": cog})
        if not data or data[0] != "Success":
            await ctx.send(embed=discord.Embed(description=f"Error: {data[0]}", colour=self.bot.error_colour))
        else:
            await ctx.send(
                embed=discord.Embed(description="Successfully reloaded the module.", colour=self.bot.primary_colour)
            )

    @checks.is_owner()
    @commands.command(description="Reload a library.", usage="reloadlib", hidden=True)
    async def reloadlib(self, ctx, *, lib: str):
        data = await self.bot.comm.handler("reload_import", self.bot.cluster_count, {"lib": lib})
        if not data or data[0] != "Success":
            await ctx.send(embed=discord.Embed(description=f"Error: {data[0]}", colour=self.bot.error_colour))
        else:
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully reloaded the library.",
                    colour=self.bot.primary_colour,
                )
            )

    @checks.is_owner()
    @commands.command(name="eval", description="Evaluate code.", usage="eval <code>", hidden=True)
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
            await ctx.send(
                embed=discord.Embed(
                    description=f"```py\n{e.__class__.__name__}: {e}\n```",
                    colour=self.bot.primary_colour,
                )
            )
            return
        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(
                embed=discord.Embed(
                    description=f"```py\n{value}{traceback.format_exc()}\n```",
                    colour=self.bot.error_colour,
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
                        embed=discord.Embed(description=f"```py\n{value}\n```", colour=self.bot.primary_colour)
                    )
            else:
                self._last_result = ret
                await ctx.send(
                    embed=discord.Embed(description=f"```py\n{value}{ret}\n```", colour=self.bot.primary_colour)
                )

    @checks.is_owner()
    @commands.command(description="Evaluate code on all clusters", usage="evall <code>", hidden=True)
    async def evall(self, ctx, *, code: str):
        data = "\n".join(
            await self.bot.comm.handler("evaluate", self.bot.cluster_count, {"code": code})
        )
        if len(data) > 2000:
            data = data[:1997] + "..."
        await ctx.send(embed=discord.Embed(description=data, colour=self.bot.primary_colour))

    @checks.is_owner()
    @commands.command(description="Execute code in bash.", usage="bash <command>", hidden=True)
    async def bash(self, ctx, *, command_to_run: str):
        try:
            output = subprocess.check_output(command_to_run.split(), stderr=subprocess.STDOUT).decode("utf-8")
            await ctx.send(embed=discord.Embed(description=f"```py\n{output}\n```", colour=self.bot.primary_colour))
        except Exception as error:
            await ctx.send(
                embed=discord.Embed(
                    description=f"```py\n{error.__class__.__name__}: {error}\n```",
                    colour=self.bot.error_colour,
                )
            )

    @checks.is_owner()
    @commands.command(description="Execute SQL.", usage="sql <query>", hidden=True)
    async def sql(self, ctx, *, query: str):
        async with self.bot.pool.acquire() as conn:
            try:
                res = await conn.fetch(query)
            except Exception:
                await ctx.send(
                    embed=discord.Embed(description=f"```py\n{traceback.format_exc()}```", colour=self.bot.error_colour)
                )
                return
        if res:
            await ctx.send(embed=discord.Embed(description=f"```{res}```", colour=self.bot.primary_colour))
        else:
            await ctx.send(embed=discord.Embed(description="No results to fetch.", colour=self.bot.primary_colour))

    @checks.is_owner()
    @commands.command(
        description="Invoke the command as another user and optionally in another channel.",
        usage="invoke [channel] <user> <command>",
        hidden=True,
    )
    async def invoke(self, ctx, channel: Optional[discord.TextChannel], user: converters.GlobalUser, *, command: str):
        msg = copy.copy(ctx.message)
        channel = channel or ctx.channel
        msg.channel = channel
        msg.author = channel.guild.get_member(user.id) or user
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @checks.is_owner()
    @commands.command(description="Give a user temporary premium.", usage="givepremium <user> <expiry>", hidden=True)
    async def givepremium(self, ctx, user: converters.GlobalUser, *, expiry: converters.DateTime):
        premium = await self.bot.tools.get_premium_slots(self.bot, user.id)
        if premium:
            await ctx.send(
                embed=discord.Embed(description="That user already has premium.", colour=self.bot.error_colour)
            )
            return
        async with self.bot.pool.acquire() as conn:
            timestamp = int(expiry.replace(tzinfo=timezone.utc).timestamp() * 1000)
            await conn.execute(
                "INSERT INTO premium (identifier, guild, expiry) VALUES ($1, $2, $3)", user.id, [], timestamp
            )
        await ctx.send(
            embed=discord.Embed(
                description="Successfully assigned that user premium temporarily.",
                colour=self.bot.primary_colour,
            )
        )

    @checks.is_owner()
    @commands.command(description="Remove a user's premium.", usage="wipepremium <user>", hidden=True)
    async def wipepremium(self, ctx, *, user: converters.GlobalUser):
        await self.bot.tools.wipe_premium(self.bot, user.id)
        await ctx.send(
            embed=discord.Embed(
                description="Successfully removed that user's premium.",
                colour=self.bot.primary_colour,
            )
        )

    @checks.is_owner()
    @commands.command(description="Ban a user from the bot", usage="banuser <user>", hidden=True)
    async def banuser(self, ctx, *, user: converters.GlobalUser):
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT * FROM ban WHERE identifier=$1 AND category=$2", user.id, 0)
            if res:
                await ctx.send(
                    embed=discord.Embed(description="That user is already banned.", colour=self.bot.error_colour)
                )
                return
            await conn.execute("INSERT INTO ban (identifier, category) VALUES ($1, $2)", user.id, 0)
        self.bot.banned_users.append(user.id)
        await ctx.send(
            embed=discord.Embed(
                description="Successfully banned that user from the bot.",
                colour=self.bot.primary_colour,
            )
        )

    @checks.is_owner()
    @commands.command(description="Unban a user from the bot", usage="unbanuser <user>", hidden=True)
    async def unbanuser(self, ctx, *, user: int):
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT * FROM ban WHERE identifier=$1 AND category=$2", user, 0)
            if not res:
                await ctx.send(
                    embed=discord.Embed(description="That user is not already banned.", colour=self.bot.error_colour)
                )
                return
            await conn.execute("DELETE FROM ban WHERE identifier=$1 AND category=$2", user, 0)
        self.bot.banned_users.remove(user)
        await ctx.send(
            embed=discord.Embed(
                description="Successfully unbanned that user from the bot.",
                colour=self.bot.primary_colour,
            )
        )

    @checks.is_owner()
    @commands.command(description="Make the bot leave a server.", usage="leaveserver <server ID>", hidden=True)
    async def leaveserver(self, ctx, *, guild: converters.GlobalGuild):
        await self.bot.comm.handler("leave_guild", -1, {"guild_id": guild.id})
        await ctx.send(embed=discord.Embed(description="The bot has left that server.", colour=self.bot.primary_colour))

    @checks.is_owner()
    @commands.command(description="Ban a server from the bot", usage="banserver <server ID>", hidden=True)
    async def banserver(self, ctx, *, guild: converters.GlobalGuild):
        await self.bot.comm.handler("leave_guild", -1, {"guild_id": guild.id})
        async with self.bot.pool.acquire() as conn:
            await conn.execute("INSERT INTO ban (identifier, category) VALUES ($1, $2)", guild.id, 1)
        self.bot.banned_guilds.append(guild.id)
        await ctx.send(
            embed=discord.Embed(
                description="Successfully banned that server from the bot.",
                colour=self.bot.primary_colour,
            )
        )

    @checks.is_owner()
    @commands.command(description="Unban a server from the bot", usage="unbanserver <server ID>", hidden=True)
    async def unbanserver(self, ctx, *, guild: int):
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT * FROM ban WHERE identifier=$1 AND category=$2", guild, 1)
            if not res:
                await ctx.send(
                    embed=discord.Embed(description="That server is not already banned.", colour=self.bot.error_colour)
                )
                return
            await conn.execute("DELETE FROM ban WHERE identifier=$1 AND category=$2", guild, 1)
        self.bot.banned_guilds.remove(guild)
        await ctx.send(
            embed=discord.Embed(
                description="Successfully unbanned that server from the bot.",
                colour=self.bot.primary_colour,
            )
        )


def setup(bot):
    bot.add_cog(Owner(bot))

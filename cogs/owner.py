import copy
import io
import logging
import subprocess
import textwrap
import traceback
import typing

from contextlib import redirect_stdout

import discord

from discord.ext import commands

from classes.embed import Embed, ErrorEmbed
from utils import checks
from utils.converters import ChannelConverter, GuildConverter, MemberConverter, UserConverter

log = logging.getLogger(__name__)


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_owner()
    @commands.command(name="eval", description="Evaluate code.", usage="eval <code>")
    async def _eval(self, ctx, *, body: str):
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
        }
        env.update(globals())

        if body.startswith("```") and body.endswith("```"):
            body = "\n".join(body.split("\n")[1:-1])
        body = body.strip("` \n")

        try:
            exec(f"async def func():\n{textwrap.indent(body, '  ')}", env)
        except Exception as e:
            await ctx.send(ErrorEmbed(f"```py\n{e.__class__.__name__}: {e}\n```"))
            return

        func = env["func"]
        stdout = io.StringIO()

        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            await ctx.send(ErrorEmbed(f"```py\n{stdout.getvalue()}{traceback.format_exc()}\n```"))
            return

        try:
            await ctx.message.add_reaction("✅")
        except discord.Forbidden:
            pass

        value = stdout.getvalue()

        if ret is not None:
            await ctx.send(Embed(f"```py\n{value}{ret}\n```"))
        elif value is not None:
            await ctx.send(Embed(f"```py\n{value}\n```"))

    @checks.is_owner()
    @commands.command(description="Execute code in bash.", usage="bash <command>")
    async def bash(self, ctx, *, command: str):
        try:
            output = subprocess.check_output(command.split(), stderr=subprocess.STDOUT).decode(
                "utf-8"
            )
            await ctx.send(Embed(f"```py\n{output}\n```"))
        except Exception as error:
            await ctx.send(ErrorEmbed(f"```py\n{error.__class__.__name__}: {error}\n```"))

    @checks.is_owner()
    @commands.command(description="Execute SQL query.", usage="sql <query>")
    async def sql(self, ctx, *, query: str):
        async with self.bot.pool.acquire() as conn:
            try:
                res = await conn.fetch(query)
            except Exception:
                await ctx.send(ErrorEmbed(f"```py\n{traceback.format_exc()}```"))
                return

        if res:
            await ctx.send(Embed(f"```{res}```"))
            return

        await ctx.send(Embed("No results to fetch."))

    @checks.is_owner()
    @commands.command(
        description="Invoke the command as another user and optionally in another channel.",
        usage="invoke [channel] <member> <command>",
    )
    async def invoke(
        self,
        ctx,
        channel: typing.Optional[ChannelConverter],
        member: MemberConverter,
        *,
        command: str,
    ):
        msg = copy.copy(ctx.message)
        channel = channel or ctx.channel
        msg.channel = channel
        msg.author = member
        msg.member = member
        msg.content = ctx.prefix + command

        await self.bot.invoke(await self.bot.get_context(msg, cls=type(ctx)))

    @checks.is_owner()
    @commands.command(description="Ban a user from the bot", usage="banuser <user>")
    async def banuser(self, ctx, *, user: UserConverter):
        async with self.bot.pool.acquire() as conn:
            await conn.execute("INSERT INTO ban VALUES ($1, $2)", user.id, 0)

        await self.bot.state.sadd("banned_users", user.id)

        await ctx.send(Embed("Successfully banned that user from the bot."))

    @checks.is_owner()
    @commands.command(description="Unban a user from the bot", usage="unbanuser <user>")
    async def unbanuser(self, ctx, *, user: UserConverter):
        async with self.bot.pool.acquire() as conn:
            res = await conn.execute(
                "DELETE FROM ban WHERE identifier=$1 AND category=$2", user.id, 0
            )

        if res == "DELETE 0":
            await ctx.send(ErrorEmbed("That user is not banned."))
            return

        await self.bot.state.srem("banned_users", user.id)

        await ctx.send(Embed("Successfully unbanned that user from the bot."))

    @checks.is_owner()
    @commands.command(description="Ban a server from the bot", usage="banserver <server ID>")
    async def banserver(self, ctx, *, guild: GuildConverter):
        async with self.bot.pool.acquire() as conn:
            await conn.execute("INSERT INTO ban VALUES ($1, $2)", guild.id, 1)

        await self.bot.state.sadd("banned_guilds", guild.id)

        await ctx.send(Embed("Successfully banned that server from the bot."))

    @checks.is_owner()
    @commands.command(description="Unban a server from the bot", usage="unbanserver <server ID>")
    async def unbanserver(self, ctx, *, guild: int):
        async with self.bot.pool.acquire() as conn:
            res = await conn.execute(
                "DELETE FROM ban WHERE identifier=$1 AND category=$2", guild, 1
            )

        if res == "DELETE 0":
            await ctx.send(ErrorEmbed("That server is not banned."))
            return

        await self.bot.state.srem("banned_guilds", guild)

        await ctx.send(Embed("Successfully unbanned that server from the bot."))


def setup(bot):
    bot.add_cog(Owner(bot))

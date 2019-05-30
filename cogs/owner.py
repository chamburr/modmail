import copy
import discord
import traceback
import textwrap
import io
import subprocess

from typing import Optional
from contextlib import redirect_stdout
from discord.ext import commands

import utils.checks as checks


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    @checks.is_owner()
    @commands.command(
        description="Load a module.",
        usage="load <cog>",
        hidden=True,
    )
    async def load(self, ctx, *, cog: str):
        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    description=f"ERROR: {type(e).__name__} - {e}",
                    color=self.bot.primary_colour,
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully loaded the module.",
                    color=self.bot.primary_colour,
                )
            )

    @checks.is_owner()
    @commands.command(
        description="Unload a module.",
        usage="unload <cog>",
        hidden=True,
    )
    async def unload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    description=f"ERROR: {type(e).__name__} - {e}",
                    color=self.bot.primary_colour,
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully unloaded the module.",
                    color=self.bot.primary_colour,
                )
            )

    @checks.is_owner()
    @commands.command(
        description="Reload a module.",
        usage="reload <cog>",
        hidden=True,
    )
    async def reload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    description=f"ERROR: {type(e).__name__} - {e}",
                    color=self.bot.primary_colour,
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully reloaded the module.",
                    color=self.bot.primary_colour,
                )
            )

    @commands.is_owner()
    @commands.command(
        description="Restart the bot.",
        usage="restart",
        hidden=True,
    )
    async def restart(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                description="Restarting...",
                color=self.bot.primary_colour,
            )
        )
        await self.bot.logout()

    def cleanup_code(self, content):
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])
        return content.strip("` \n")

    @checks.is_owner()
    @commands.command(
        name="eval",
        description="Evaluate a code",
        usage="eval <code>",
        hidden=True,
    )
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

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"```py\n{e.__class__.__name__}: {e}\n```",
                    color=self.bot.primary_colour,
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
                    description=f"```py\n{value}{traceback.format_exc()}\n```",
                    color=self.bot.primary_colour,
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
                        embed=discord.Embed(
                            descrption=f"```py\n{value}\n```",
                            color=self.bot.primary_colour,
                        )
                    )
            else:
                self._last_result = ret
                await ctx.send(
                    embed=discord.Embed(
                        description=f"```py\n{value}{ret}\n```",
                        color=self.bot.primary_colour,
                    )
                )

    @checks.is_owner()
    @commands.command(
        description="Execute code in bash.",
        usage="bash <command>",
        hidden=True,
    )
    async def bash(self, ctx, *, command_to_run: str):
        output = subprocess.check_output(
            command_to_run.split(), stderr=subprocess.STDOUT
        ).decode("utf-8")
        await ctx.send(
            embed=discord.Embed(
                description=f"```py\n{output}\n```",
                color=self.bot.primary_colour,
            )
        )

    @checks.is_owner()
    @commands.command(
        description="Execute SQL.",
        usage="sql <query>",
        hidden=True,
    )
    async def sql(self, ctx, *, query: str):
        c = self.bot.conn.cursor()
        try:
            c.execute(query)
            res = c.fetchone()
            self.bot.conn.commit()
        except Exception:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"```py\n{traceback.format_exc()}```",
                    color=self.bot.primary_colour,
                )
            )
        if res:
            await ctx.send(
                embed=discord.Embed(
                    description=f"```{res}```",
                    color=self.bot.primary_colour,
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    description="No results to fetch.",
                    color=self.bot.primary_colour,
                )
            )

    @checks.is_owner()
    @commands.command(
        description="Get the bot logs. Default to 10 lines.",
        usage="botlogs [lines]",
        hideen=True,
    )
    async def botlogs(self, ctx, *, lines: int = 10):
        with open("discord.log", "r") as file:
            content = file.readlines()
        if lines > len(content):
            lines = len(content)
        content = "\n".join(content[(len(content) - lines):])
        try:
            await ctx.send(
                embed=discord.Embed(
                    description=f"```{content}```",
                    color=self.bot.primary_colour,
                )
            )
        except discord.HTTPException:
            await ctx.send(
                embed=discord.Embed(
                    description="The message is too long to be sent.",
                    color=self.bot.error_colour,
                )
            )

    @checks.is_owner()
    @commands.command(
        description="Invoke the command as another user and optionally in another channel.",
        usage="invoke [channel] <user> <command>",
        hidden=True,
    )
    async def invoke(self, ctx, channel: Optional[discord.TextChannel], who: discord.User, *, command: str):
        msg = copy.copy(ctx.message)
        channel = channel or ctx.channel
        msg.channel = channel
        msg.author = channel.guild.get_member(who.id) or who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @checks.is_owner()
    @commands.command(
        description="Make me say something.",
        usage="echo <message>",
        rest_is_raw=True,
        hidden=True,
    )
    async def echo(self, ctx, *, content):
        await ctx.send(content)

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers with the specified name.",
        usage="findserver <name>",
        hidden=True,
    )
    async def findserver(self, ctx, *, name: str):
        guilds = []
        for guild in self.bot.guilds:
            if guild.name.lower().count(name.lower()) > 0:
                guilds.append(f"{guild.name} `{guild.id}`")
        if len(guilds) == 0:
            await ctx.send(
                embed=discord.Embed(
                    description="No such guild was found.",
                    color=self.bot.error_colour,
                )
            )
        else:
            try:
                await ctx.send(
                    embed=discord.Embed(
                        description="\n".join(guilds),
                        color=self.bot.primary_colour,
                    )
                )
            except discord.HTTPException:
                await ctx.send(
                    embed=discord.Embed(
                        description="The message is too long to be sent.",
                        color=self.bot.error_colour,
                    )
                )

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers the bot shares with the user.",
        usage="sharedservers <user>"
    )
    async def sharedservers(self, ctx, *, user: discord.User):
        guilds = []
        for guild in self.bot.guilds:
            if guild.get_member(user.id) is not None:
                guilds.append(f"{guild.name} `{guild.id}`{' (Owner)' if guild.owner_id == user.id else ''}")
        if len(guilds) == 0:
            await ctx.send(
                embed=discord.Embed(
                    description="No such guild was found.",
                    color=self.bot.error_colour,
                )
            )
        else:
            try:
                await ctx.send(
                    embed=discord.Embed(
                        description="\n".join(guilds),
                        color=self.bot.primary_colour,
                    )
                )
            except discord.HTTPException:
                await ctx.send(
                    embed=discord.Embed(
                        description="The message is too long to be sent.",
                        color=self.bot.error_colour,
                    )
                )

    @checks.is_admin()
    @commands.command(
        description="Create an invite to the specified server.",
        usage="createinvite <server id>",
        hidden=True,
    )
    async def createinvite(self, ctx, *, guild_id: int):
        for guild in self.bot.guilds:
            if guild.id == guild_id:
                try:
                    invite = (await guild.invites())[0]
                    return await ctx.send(
                        embed=discord.Embed(
                            description=f"Found invite created by {invite.inviter.name}: {invite.url}.",
                            color=self.bot.primary_colour,
                        )
                    )
                except (IndexError, discord.Forbidden):
                    try:
                        return await ctx.send(
                            embed=discord.Embed(
                                description="Created an invite to the server that will expire in 120 seconds: "
                                            f"{(await guild.text_channels[0].create_invite(max_age=120)).url}.",
                                color=self.bot.primary_colour,
                            )
                        )
                    except discord.Forbidden:
                        return await ctx.send(
                            embed=discord.Embed(
                                description="No permissions to create an invite link.",
                                color=self.bot.primary_colour,
                            )
                        )
        await ctx.send(
            embed=discord.Embed(
                description="No such guild was found.",
                color=self.bot.primary_colour,
            )
        )


def setup(bot):
    bot.add_cog(Owner(bot))

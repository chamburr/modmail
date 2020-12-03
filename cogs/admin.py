import json
import logging

from typing import Optional

import discord

from discord.ext import commands

from classes import converters
from utils import checks
from utils.paginator import Paginator

log = logging.getLogger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers with the specified name.",
        usage="findserver <name>",
        hidden=True,
    )
    async def findserver(self, ctx, *, name: str):
        data = await self.bot.comm.handler("find_guild", self.bot.cluster_count, {"name": name})
        guilds = []
        for chunk in data:
            guilds.extend(chunk)
        guilds = [f"{guild.name} `{guild.id}` ({guild.member_count} members)" for guild in guilds]
        if len(guilds) == 0:
            await ctx.send(embed=discord.Embed(description="No such guild was found.", colour=self.bot.error_colour))
            return
        all_pages = []
        for chunk in [guilds[i : i + 20] for i in range(0, len(guilds), 20)]:
            page = discord.Embed(title="Servers", colour=self.bot.primary_colour)
            for guild in chunk:
                if page.description == discord.Embed.Empty:
                    page.description = guild
                else:
                    page.description += f"\n{guild}"
            page.set_footer(text="Use the reactions to flip pages.")
            all_pages.append(page)
        if len(all_pages) == 1:
            embed = all_pages[0]
            embed.set_footer(text=discord.Embed.Empty)
            await ctx.send(embed=embed)
            return
        paginator = Paginator(length=1, entries=all_pages, use_defaults=True, embed=True, timeout=120)
        await paginator.start(ctx)

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers the bot shares with the user.",
        usage="sharedservers <user>",
        hidden=True,
    )
    async def sharedservers(self, ctx, *, user: converters.GlobalUser):
        data = await self.bot.comm.handler(
            "get_user_guilds", self.bot.cluster_count, {"user_id": user.id}
        )
        guilds = []
        for chunk in data:
            guilds.extend(chunk)
        guilds = [f"{guild.name} `{guild.id}` ({guild.member_count} members)" for guild in guilds]
        all_pages = []
        for chunk in [guilds[i : i + 20] for i in range(0, len(guilds), 20)]:
            page = discord.Embed(title="Servers", colour=self.bot.primary_colour)
            for guild in chunk:
                if page.description == discord.Embed.Empty:
                    page.description = guild
                else:
                    page.description += f"\n{guild}"
            page.set_footer(text="Use the reactions to flip pages.")
            all_pages.append(page)
        if len(all_pages) == 1:
            embed = all_pages[0]
            embed.set_footer(text=discord.Embed.Empty)
            await ctx.send(embed=embed)
            return
        paginator = Paginator(length=1, entries=all_pages, use_defaults=True, embed=True, timeout=120)
        await paginator.start(ctx)

    @checks.is_admin()
    @commands.command(
        description="Create an invite to the specified server.",
        usage="createinvite <server ID>",
        hidden=True,
    )
    async def createinvite(self, ctx, *, guild: converters.GlobalGuild):
        invite = await self.bot.comm.handler("invite_guild", -1, {"guild_id": guild.id})
        if not invite:
            await ctx.send(
                embed=discord.Embed(
                    description="No permissions to create an invite link.",
                    colour=self.bot.primary_colour,
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    description=f"Here is the invite link: https://discord.gg/{invite.code}",
                    colour=self.bot.primary_colour,
                )
            )

    @checks.is_admin()
    @commands.command(
        description="Get the top servers using the bot.",
        aliases=["topguilds"],
        usage="topservers [count]",
        hidden=True,
    )
    async def topservers(self, ctx, *, count: int = 20):
        data = await self.bot.comm.handler("get_top_guilds", self.bot.cluster_count, {"count": count})
        guilds = []
        for chunk in data:
            guilds.extend(chunk)
        guilds = sorted(guilds, key=lambda x: x.member_count, reverse=True)[:count]
        top_guilds = []
        for index, guild in enumerate(guilds):
            top_guilds.append(f"#{index + 1} {guild.name} `{guild.id}` ({guild.member_count} members)")
        all_pages = []
        for chunk in [top_guilds[i : i + 20] for i in range(0, len(top_guilds), 20)]:
            page = discord.Embed(title="Top Servers", colour=self.bot.primary_colour)
            for guild in chunk:
                if page.description == discord.Embed.Empty:
                    page.description = guild
                else:
                    page.description += f"\n{guild}"
            page.set_footer(text="Use the reactions to flip pages.")
            all_pages.append(page)
        if len(all_pages) == 1:
            embed = all_pages[0]
            embed.set_footer(text=discord.Embed.Empty)
            await ctx.send(embed=embed)
            return
        paginator = Paginator(length=1, entries=all_pages, use_defaults=True, embed=True, timeout=120)
        await paginator.start(ctx)

    @checks.is_admin()
    @commands.command(description="Make me say something.", usage="echo [channel] <message>", hidden=True)
    async def echo(self, ctx, channel: Optional[discord.TextChannel], *, content: str):
        channel = channel or ctx.channel
        await ctx.message.delete()
        await channel.send(content, allowed_mentions=discord.AllowedMentions(everyone=False))

    @checks.is_admin()
    @commands.command(description="Restart a cluster.", usage="restart <cluster>", hidden=True)
    async def restart(self, ctx, *, cluster: int):
        await ctx.send(embed=discord.Embed(description="Restarting...", colour=self.bot.primary_colour))
        await self.bot.comm.handler("restart", 0, scope="launcher", cluster=cluster)

    @checks.is_admin()
    @commands.command(description="Start a cluster.", usage="start <cluster>", hidden=True)
    async def start(self, ctx, *, cluster: int):
        await ctx.send(embed=discord.Embed(description="Starting...", colour=self.bot.primary_colour))
        await self.bot.comm.handler("start", 0, scope="launcher", cluster=cluster)

    @checks.is_admin()
    @commands.command(description="Stop a cluster.", usage="stop <cluster>", hidden=True)
    async def stop(self, ctx, *, cluster: int):
        await ctx.send(embed=discord.Embed(description="Stopping...", colour=self.bot.primary_colour))
        await self.bot.comm.handler("stop", 0, scope="launcher", cluster=cluster)

    @checks.is_admin()
    @commands.command(description="Perform a rolling restart.", usage="rollrestart", hidden=True)
    async def rollrestart(self, ctx):
        await ctx.send(embed=discord.Embed(description="Rolling a restart...", colour=self.bot.primary_colour))
        await self.bot.comm.handler("roll_restart", 0, scope="launcher")

    @checks.is_admin()
    @commands.command(description="Get clusters' statuses.", usage="status", hidden=True)
    async def status(self, ctx):
        data = await self.bot.comm.handler("get_status", self.bot.cluster_count)
        data = [list(vars(x).items()) for x in data]
        data = sorted([(int(x[0]), x[1]) for y in data for x in y], key=lambda x: x[0])
        clusters = {}
        for x in data:
            clusters[x[0]] = x[1]
        await ctx.send(
            embed=discord.Embed(
                description=f"```json\n{json.dumps(clusters, indent=4, default=lambda o: o.__dict__)}```",
                colour=self.bot.primary_colour,
            )
        )


def setup(bot):
    bot.add_cog(Admin(bot))

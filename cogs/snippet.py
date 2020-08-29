import logging

import discord

from discord.ext import commands

from cogs.modmail_channel import ModMailEvents
from utils import checks
from utils.paginator import Paginator

log = logging.getLogger(__name__)


class Snippet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_premium()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Use a snippet.", aliases=["s"], usage="snippet <name>")
    async def snippet(self, ctx, *, name: str):
        name = name.lower()
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT content FROM snippet WHERE name=$1 AND guild=$2", name, ctx.guild.id)
        if not res:
            await ctx.send(embed=discord.Embed(description="The snippet was not found.", colour=self.bot.error_colour))
            return
        modmail = ModMailEvents(self.bot)
        await modmail.send_mail_mod(ctx.message, ctx.prefix, False, res[0], True)

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_premium()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Use a snippet anonymously.", aliases=["as"], usage="asnippet <name>")
    async def asnippet(self, ctx, *, name: str):
        name = name.lower()
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT content FROM snippet WHERE name=$1 AND guild=$2", name, ctx.guild.id)
        if not res:
            await ctx.send(embed=discord.Embed(description="The snippet was not found.", colour=self.bot.error_colour))
            return
        modmail = ModMailEvents(self.bot)
        await modmail.send_mail_mod(ctx.message, ctx.prefix, True, res[0], True)

    @checks.in_database()
    @checks.is_premium()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Add a snippet. Tags `{username}`, `{usertag}`, `{userid}` and `{usermention}` can be used.",
        usage="snippetadd <name> <content>",
    )
    async def snippetadd(self, ctx, name: str, *, content: str):
        name = name.lower()
        if len(name) > 100:
            await ctx.send(
                embed=discord.Embed(
                    description="The snippet name cannot exceed 100 characters.",
                    colour=self.bot.error_colour,
                )
            )
            return
        if len(content) > 1000:
            await ctx.send(
                embed=discord.Embed(
                    description="The snippet content cannot exceed 1000 characters.",
                    colour=self.bot.error_colour,
                )
            )
            return
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT content FROM snippet WHERE name=$1 AND guild=$2", name, ctx.guild.id)
            if res:
                await ctx.send(
                    embed=discord.Embed(
                        description="A snippet with that name already exists.",
                        colour=self.bot.error_colour,
                    )
                )
                return
            await conn.execute("INSERT INTO snippet VALUES ($1, $2, $3)", ctx.guild.id, name, content)
        await ctx.send(
            embed=discord.Embed(description="The snippet was added successfully.", colour=self.bot.primary_colour)
        )

    @checks.in_database()
    @checks.is_premium()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Remove a snippet.", usage="snippetremove <name>")
    async def snippetremove(self, ctx, *, name: str):
        name = name.lower()
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT content FROM snippet WHERE name=$1 AND guild=$2", name, ctx.guild.id)
            if not res:
                await ctx.send(
                    embed=discord.Embed(
                        description="A snippet with that name was not found.",
                        colour=self.bot.error_colour,
                    )
                )
                return
            await conn.execute("DELETE FROM snippet WHERE name=$1 AND guild=$2", name, ctx.guild.id)
        await ctx.send(
            embed=discord.Embed(description="The snippet was removed successfully.", colour=self.bot.primary_colour)
        )

    @checks.in_database()
    @checks.is_premium()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Remove all the snippets.", usage="snippetclear")
    async def snippetclear(self, ctx):
        async with self.bot.pool.acquire() as conn:
            await conn.execute("DELETE FROM snippet WHERE guild=$1", ctx.guild.id)
        await ctx.send(
            embed=discord.Embed(
                description="All snippets have been removed successfully.",
                colour=self.bot.primary_colour,
            )
        )

    @checks.in_database()
    @checks.is_premium()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="View all the snippets or a specific one if specified.",
        aliases=["viewsnippets", "snippetlist"],
        usage="viewsnippet [name]",
    )
    async def viewsnippet(self, ctx, *, name: str = None):
        if name:
            name = name.lower()
            async with self.bot.pool.acquire() as conn:
                res = await conn.fetchrow(
                    "SELECT name, content FROM snippet WHERE name=$1 AND guild=$2",
                    name,
                    ctx.guild.id,
                )
            if not res:
                await ctx.send(
                    embed=discord.Embed(
                        description="A snippet with that name was not found.",
                        colour=self.bot.error_colour,
                    )
                )
                return
            embed = discord.Embed(title="Snippet", colour=self.bot.primary_colour)
            embed.add_field(name="Name", value=res[0], inline=False)
            embed.add_field(name="Content", value=res[1], inline=False)
            await ctx.send(embed=embed)
            return
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetch("SELECT name, content FROM snippet WHERE guild=$1", ctx.guild.id)
        if not res:
            await ctx.send(
                embed=discord.Embed(description="No snippet has been added yet.", colour=self.bot.primary_colour)
            )
            return
        all_pages = []
        for chunk in [res[i : i + 10] for i in range(0, len(res), 10)]:
            page = discord.Embed(title="Snippets", colour=self.bot.primary_colour)
            for snippet in chunk:
                page.add_field(
                    name=snippet[0],
                    value=snippet[1][:100] + "..." if len(snippet[1]) > 100 else snippet[1],
                    inline=False,
                )
            page.set_footer(text="Use the reactions to flip pages.")
            all_pages.append(page)
        if len(all_pages) == 1:
            embed = all_pages[0]
            embed.set_footer(text=discord.Embed.Empty)
            await ctx.send(embed=embed)
            return
        paginator = Paginator(length=1, entries=all_pages, use_defaults=True, embed=True, timeout=120)
        await paginator.start(ctx)


def setup(bot):
    bot.add_cog(Snippet(bot))

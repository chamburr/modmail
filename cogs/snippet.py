import logging

import asyncpg
import discord

from discord.ext import commands

from classes.embed import Embed, ErrorEmbed
from utils import checks, tools

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
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow(
                "SELECT content FROM snippet WHERE name=$1 AND guild=$2", name.lower(), ctx.guild.id
            )

        if not res:
            await ctx.send(ErrorEmbed("The snippet was not found."))
            return

        ctx.message.content = res[0]
        await self.bot.cogs["ModMailEvents"].send_mail_mod(
            ctx.message, ctx.prefix, anon=False, snippet=True
        )

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_premium()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Use a snippet anonymously.", aliases=["as"], usage="asnippet <name>"
    )
    async def asnippet(self, ctx, *, name: str):
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow(
                "SELECT content FROM snippet WHERE name=$1 AND guild=$2", name.lower(), ctx.guild.id
            )

        if not res:
            await ctx.send(ErrorEmbed("The snippet was not found."))
            return

        ctx.message.content = res[0]
        await self.bot.cogs["ModMailEvents"].send_mail_mod(
            ctx.message, ctx.prefix, anon=True, snippet=True
        )

    @checks.in_database()
    @checks.is_premium()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Add a snippet. Tags `{username}`, `{usertag}`, `{userid}` and `{usermention}` "
        "can be used.",
        usage="snippetadd <name> <content>",
    )
    async def snippetadd(self, ctx, name: str, *, content: str):
        if len(name) > 100:
            await ctx.send(ErrorEmbed("The snippet name cannot exceed 100 characters."))
            return

        if len(content) > 1000:
            await ctx.send(ErrorEmbed("The snippet content cannot exceed 1000 characters."))
            return

        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO snippet VALUES ($1, $2, $3, $4)",
                    ctx.guild.id,
                    name.lower(),
                    content,
                    ctx.author.id,
                )
            except asyncpg.UniqueViolationError:
                await ctx.send(ErrorEmbed("A snippet with that name already exists."))
                return

        await ctx.send(Embed("The snippet was added successfully."))

    @checks.in_database()
    @checks.is_premium()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Remove a snippet.", usage="snippetremove <name>")
    async def snippetremove(self, ctx, *, name: str):
        async with self.bot.pool.acquire() as conn:
            res = await conn.execute(
                "DELETE FROM snippet WHERE name=$1 AND guild=$2", name, ctx.guild.id
            )

        if res == "DELETE 0":
            await ctx.send(ErrorEmbed("A snippet with that name was not found."))
            return

        await ctx.send(Embed("The snippet was removed successfully."))

    @checks.in_database()
    @checks.is_premium()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Remove all the snippets.", usage="snippetclear")
    async def snippetclear(self, ctx):
        async with self.bot.pool.acquire() as conn:
            await conn.execute("DELETE FROM snippet WHERE guild=$1", ctx.guild.id)

        await ctx.send(Embed("All snippets were removed successfully."))

    @checks.in_database()
    @checks.is_premium()
    @checks.is_mod()
    @checks.bot_has_permissions(add_reactions=True)
    @commands.guild_only()
    @commands.command(
        description="View all the snippets or a specific one if specified.",
        aliases=["viewsnippets", "snippetlist"],
        usage="viewsnippet [name]",
    )
    async def viewsnippet(self, ctx, *, name: str = None):
        if name:
            async with self.bot.pool.acquire() as conn:
                res = await conn.fetchrow(
                    "SELECT name, content, author FROM snippet WHERE name=$1 AND guild=$2",
                    name.lower(),
                    ctx.guild.id,
                )

            if not res:
                await ctx.send(ErrorEmbed("A snippet with that name was not found."))
                return

            embed = Embed(title="Snippet")
            embed.add_field("Name", res[0], False)
            embed.add_field("Content", res[1], False)
            embed.add_field("Author", f"<@{res[2]}>" if res[2] is not None else "Unknown", False)
            await ctx.send(embed)
            return

        async with self.bot.pool.acquire() as conn:
            res = await conn.fetch(
                "SELECT name, content, author FROM snippet WHERE guild=$1", ctx.guild.id
            )

        if not res:
            await ctx.send(Embed("No snippet has been added yet."))
            return

        all_pages = []
        for chunk in [res[i : i + 10] for i in range(0, len(res), 10)]:
            page = Embed(title="Snippets")

            for snippet in chunk:
                page.add_field(
                    snippet[0],
                    snippet[1][:97] + "..." if len(snippet[1]) > 100 else snippet[1],
                    False,
                )

            page.set_footer("Use the reactions to flip pages.")
            all_pages.append(page)

        if len(all_pages) == 1:
            embed = all_pages[0]
            embed.set_footer(discord.Embed.Empty)
            await ctx.send(embed)
            return

        await tools.create_paginator(self.bot, ctx, all_pages)


def setup(bot):
    bot.add_cog(Snippet(bot))

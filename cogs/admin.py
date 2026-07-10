from __future__ import annotations

import logging

from datetime import timezone

import discord

from discord.ext import commands

from classes.bot import ModMail
from classes.context import Context
from classes.embed import Embed, ErrorEmbed
from utils import checks, tools
from utils.converters import ChannelConverter, DateTimeConverter, GuildConverter, UserConverter

log = logging.getLogger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot: ModMail) -> None:
        self.bot = bot

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers the bot shares with the user.",
        usage="sharedservers <user>",
    )
    async def sharedservers(self, ctx: Context, *, user: UserConverter) -> None:
        guilds = [
            f"{guild.name} `{guild.id}` ({guild.member_count} members)"
            for guild in [
                await self.bot.get_guild(int(guild))
                for guild in await tools.get_user_guilds(self.bot, user) or []
            ]
            if guild is not None
        ]

        if len(guilds) == 0:
            await ctx.send(ErrorEmbed("No such guild was found."))
            return

        all_pages = []

        for chunk in [guilds[i : i + 20] for i in range(0, len(guilds), 20)]:
            page = Embed(title="Shared Servers")

            for guild in chunk:
                if page.description is None:
                    page.description = guild
                else:
                    page.description += f"\n{guild}"

            page.set_footer("Use the reactions to flip pages.")
            all_pages.append(page)

        await tools.create_paginator(self.bot, ctx, all_pages)

    @checks.is_admin()
    @commands.command(
        description="Create an invite to the specified server.", usage="createinvite <server ID>"
    )
    async def createinvite(self, ctx: Context, *, guild: GuildConverter) -> None:
        try:
            invite = (await guild.invites())[0]
        except (IndexError, discord.Forbidden):
            try:
                invite = await (await guild.text_channels())[0].create_invite(max_age=120)
            except (IndexError, discord.Forbidden):
                await ctx.send(ErrorEmbed("No permissions to create an invite link."))
                return

        await ctx.send(Embed(f"Here is the invite link: {invite.url}"))

    @checks.is_admin()
    @commands.command(
        description="Give a user temporary premium.", usage="givepremium <user> <expiry>"
    )
    async def givepremium(
        self, ctx: Context, user: UserConverter, *, expiry: DateTimeConverter
    ) -> None:
        premium = await tools.get_premium_slots(self.bot, user.id)
        if premium:
            await ctx.send(ErrorEmbed("That user already has premium."))
            return

        async with self.bot.pool.acquire() as conn:
            timestamp = int(expiry.replace(tzinfo=timezone.utc).timestamp() * 1000)
            await conn.execute("INSERT INTO premium VALUES ($1, $2, $3)", user.id, [], timestamp)

        await ctx.send(Embed("Successfully assigned that user premium temporarily."))

    @checks.is_admin()
    @commands.command(description="Remove a user's premium.", usage="wipepremium <user>")
    async def wipepremium(self, ctx: Context, *, user: UserConverter) -> None:
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT guild FROM premium WHERE identifier=$1", user.id)
            if res:
                for guild in res[0]:
                    await tools.remove_premium(self.bot, guild)

            await conn.execute("DELETE FROM premium WHERE identifier=$1", user.id)

        await ctx.send(Embed("Successfully removed that user's premium."))

    @checks.is_admin()
    @commands.command(
        description="Transfer a user's premium to another user.",
        usage="transferpremium <user> <other>",
    )
    async def transferpremium(
        self, ctx: Context, user: UserConverter, *, other: UserConverter
    ) -> None:
        premium = await tools.get_premium_slots(self.bot, other.id)
        if premium:
            await ctx.send(ErrorEmbed("That user already has premium."))
            return

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE premium SET identifier=$1 WHERE identifier=$2", other.id, user.id
            )

        await ctx.send(Embed("Successfully transferred that user's premium."))

    @checks.is_admin()
    @commands.command(description="Make me say something.", usage="echo [channel] <message>")
    async def echo(self, ctx: Context, channel: ChannelConverter | None, *, content: str) -> None:
        channel = channel or ctx.channel
        await ctx.message.delete()
        await channel.send(content, allowed_mentions=discord.AllowedMentions(everyone=False))

    @checks.is_admin()
    @commands.command(description="Restart all clusters.", usage="restart")
    async def restart(self, ctx: Context) -> None:
        await ctx.send(Embed("Restarting..."))
        await self.bot.session.post(f"{self.bot.http_uri}/restart")


async def setup(bot: ModMail) -> None:
    await bot.add_cog(Admin(bot))

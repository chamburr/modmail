import logging
import typing

import discord

from discord.ext import commands

from classes.embed import Embed, ErrorEmbed
from utils import checks, tools
from utils.converters import ChannelConverter, GuildConverter, UserConverter

log = logging.getLogger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _send_guilds(self, ctx, guilds, title):
        if len(guilds) == 0:
            await ctx.send(ErrorEmbed("No such guild was found."))
            return

        all_pages = []

        for chunk in [guilds[i : i + 20] for i in range(0, len(guilds), 20)]:
            page = Embed(title=title)

            for guild in chunk:
                if page.description == discord.Embed.Empty:
                    page.description = guild
                else:
                    page.description += f"\n{guild}"

            page.set_footer("Use the reactions to flip pages.")
            all_pages.append(page)

        await tools.create_paginator(self.bot, ctx, all_pages)

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers with the specified name.", usage="findserver <name>"
    )
    async def findserver(self, ctx, *, name: str):
        guilds = [
            f"{guild.name} `{guild.id}` ({guild.member_count} members)"
            for guild in await self.bot.guilds()
            if guild.name.lower().count(name.lower()) > 0
        ]

        await self._send_guilds(ctx, guilds, "Servers")

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers the bot shares with the user.",
        usage="sharedservers <user>",
    )
    async def sharedservers(self, ctx, *, user: UserConverter):
        guilds = [
            f"{guild.name} `{guild.id}` ({guild.member_count} members)"
            for guild in [
                await self.bot.get_guild(int(guild))
                for guild in await self.bot.state.smembers(f"user_guilds:{user.id}")
            ]
        ]

        await self._send_guilds(ctx, guilds, "Shared Servers")

    @checks.is_admin()
    @commands.command(description="Get the top servers using the bot.", usage="topservers [count]")
    async def topservers(self, ctx, *, count: int = 20):
        guilds = [
            f"#{index + 1} {guild.name} `{guild.id}` ({guild.member_count} members)"
            for index, guild in enumerate(
                sorted(await self.bot.guilds(), key=lambda x: x.member_count, reverse=True)[:count]
            )
        ]

        await self._send_guilds(ctx, guilds, "Top Servers")

    @checks.is_admin()
    @commands.command(
        description="Create an invite to the specified server.", usage="createinvite <server ID>"
    )
    async def createinvite(self, ctx, *, guild: GuildConverter):
        try:
            invite = (await guild.invites())[0]
        except (IndexError, discord.Forbidden):
            try:
                invite = (await guild.text_channels())[0].create_invite(max_age=120)
            except (IndexError, discord.Forbidden):
                await ctx.send(ErrorEmbed("No permissions to create an invite link."))
                return

        await ctx.send(Embed(f"Here is the invite link: {invite.url}"))

    @checks.is_admin()
    @commands.command(description="Make me say something.", usage="echo [channel] <message>")
    async def echo(self, ctx, channel: typing.Optional[ChannelConverter], *, content: str):
        channel = channel or ctx.channel
        await ctx.message.delete()
        await channel.send(content, allowed_mentions=discord.AllowedMentions(everyone=False))

    @checks.is_admin()
    @commands.command(description="Restart all clusters.", usage="restart")
    async def restart(self, ctx):
        await ctx.send(Embed("Restarting..."))
        await self.bot.session.post(f"{self.bot.http_uri}/restart")


def setup(bot):
    bot.add_cog(Admin(bot))

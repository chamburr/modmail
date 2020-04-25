import logging

import discord

from discord.ext import commands

from utils import checks

log = logging.getLogger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers with the specified name.", usage="findserver <name>", hidden=True,
    )
    async def findserver(self, ctx, *, name: str):
        data = await self.bot.cogs["Communication"].handler("find_guild", self.bot.cluster_count, {"name": name})
        guilds = []
        for chunk in data:
            guilds.extend(chunk)
        if len(guilds) == 0:
            await ctx.send(embed=discord.Embed(description="No such guild was found.", colour=self.bot.error_colour))
            return
        try:
            await ctx.send(embed=discord.Embed(description="\n".join(guilds), colour=self.bot.primary_colour))
        except discord.HTTPException:
            await ctx.send(
                embed=discord.Embed(description="The message is too long to be sent.", colour=self.bot.error_colour)
            )

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers the bot shares with the user.", usage="sharedservers <user>", hidden=True
    )
    async def sharedservers(self, ctx, *, user_id: int):
        user = await self.bot.cogs["Communication"].handler("get_user", 1, {"user_id": user_id})
        if not user:
            await ctx.send(embed=discord.Embed(description="No such user was found.", colour=self.bot.error_colour))
            return
        data = await self.bot.cogs["Communication"].handler(
            "get_user_guilds", self.bot.cluster_count, {"user_id": user_id}
        )
        guilds = []
        for chunk in data:
            guilds.extend(chunk)
        guild_list = [f"{guild['name']} `{guild['id']}`" for guild in guilds]
        try:
            await ctx.send(embed=discord.Embed(description="\n".join(guild_list), colour=self.bot.primary_colour))
        except discord.HTTPException:
            await ctx.send(
                embed=discord.Embed(description="The message is too long to be sent.", colour=self.bot.error_colour)
            )

    @checks.is_admin()
    @commands.command(
        description="Create an invite to the specified server.", usage="createinvite <server ID>", hidden=True,
    )
    async def createinvite(self, ctx, *, guild_id: int):
        guild = await self.bot.cogs["Communication"].handler("get_guild", 1, {"guild_id": guild_id})
        if not guild:
            await ctx.send(embed=discord.Embed(description="No such guild was found.", colour=self.bot.error_colour))
            return
        invite = await self.bot.cogs["Communication"].handler("invite_guild", 1, {"guild_id": guild_id})
        if not invite:
            await ctx.send(
                embed=discord.Embed(
                    description="No permissions to create an invite link.", colour=self.bot.primary_colour,
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    description=f"Here is the invite link: https://discord.gg/{invite[0]['code']}",
                    colour=self.bot.primary_colour,
                )
            )


def setup(bot):
    bot.add_cog(Admin(bot))

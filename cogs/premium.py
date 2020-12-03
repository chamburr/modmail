import logging

import discord

from discord.ext import commands

from utils import checks

log = logging.getLogger(__name__)


class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        description="Get some information about ModMail premium.",
        usage="premium",
        aliases=["donate", "patron"],
    )
    async def premium(self, ctx):
        embed = discord.Embed(
            title="Premium",
            description="Purchasing premium is the best way you can show support to us. As hosting this bot for all "
            "the servers and users costs much money, your donation will certainly help us a lot in keeping the bot "
            "running. You will also get access to the premium features listed below.",
            colour=self.bot.primary_colour,
        )
        embed.add_field(
            name="Premium Features",
            value="- Custom greeting and closing messages.\n- Advanced logging that includes chat history.\n- Snippet "
            "functionality (saved messages).\n- Priority support.\n- Exclusive role and channels in the support server."
            "\n- More features released in future.",
            inline=False,
        )
        embed.add_field(
            name="Get Premium",
            value="Please join our support server and go to https://modmail.xyz/premium.",
            inline=False,
        )
        await ctx.send(embed=embed)

    @checks.is_premium()
    @commands.guild_only()
    @commands.command(description="Get the premium status of this server.", usage="premiumstatus")
    async def premiumstatus(self, ctx):
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetch("SELECT identifier, guild FROM premium")
        premium_servers = []
        for row in res:
            premium_servers.extend(row[1])
            if ctx.guild.id in premium_servers:
                await ctx.send(
                    embed=discord.Embed(
                        description=f"This server has premium. Offered by: <@{row[0]}>.",
                        colour=self.bot.primary_colour,
                    )
                )
                return

    @checks.is_patron()
    @commands.command(
        description="Get a list of servers you assigned premium to.",
        usage="premiumlist",
        aliases=["premiumservers", "premiumguilds"],
    )
    async def premiumlist(self, ctx):
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT guild FROM premium WHERE identifier=$1", ctx.author.id)
        if not res or not res[0]:
            await ctx.send(
                embed=discord.Embed(
                    description="You did not assign premium to any server currently.",
                    colour=self.bot.primary_colour,
                )
            )
            return
        to_send = ""
        for server in res[0]:
            guild = await self.bot.comm.handler("get_guild", -1, {"guild_id": server})
            if not guild:
                to_send += f"\nUnknown server `{server}`"
            else:
                to_send += f"\n{guild.name} `{server}`"
        await ctx.send(embed=discord.Embed(description=to_send, colour=self.bot.primary_colour))

    @checks.is_patron()
    @commands.command(description="Assign premium slot to a server.", usage="premiumassign <server ID>")
    async def premiumassign(self, ctx, *, guild: int):
        if not await self.bot.comm.handler("get_guild", -1, {"guild_id": guild}):
            await ctx.send(
                embed=discord.Embed(description="The server ID you provided is invalid.", colour=self.bot.error_colour)
            )
            return
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetch("SELECT guild FROM premium")
        all_premium = []
        for row in res:
            all_premium.extend(row[0])
        if guild in all_premium:
            await ctx.send(
                embed=discord.Embed(description="That server already has premium.", colour=self.bot.error_colour)
            )
            return
        slots = await self.bot.tools.get_premium_slots(self.bot, ctx.author.id)
        async with self.bot.pool.acquire() as conn:
            servers = await conn.fetchrow("SELECT guild FROM premium WHERE identifier=$1", ctx.author.id)
        if len(servers[0]) >= slots:
            await ctx.send(
                embed=discord.Embed(
                    description="You have reached the maximum number of slots that can be assigned. Please upgrade "
                    "your premium to increase the slots.",
                    colour=self.bot.error_colour,
                )
            )
            return
        servers[0].append(guild)
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE premium SET guild=$1 WHERE identifier=$2", servers[0], ctx.author.id)
        await ctx.send(embed=discord.Embed(description="That server now has premium.", colour=self.bot.primary_colour))

    @checks.is_patron()
    @commands.command(description="Remove premium slot from a server.", usage="premiumremove <server ID>")
    async def premiumremove(self, ctx, *, guild: int):
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT guild FROM premium WHERE identifier=$1", ctx.author.id)
        if guild not in res[0]:
            await ctx.send(
                embed=discord.Embed(
                    description="You did not assign premium to that server.",
                    colour=self.bot.error_colour,
                )
            )
            return
        servers = res[0]
        servers.remove(guild)
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE premium SET guild=$1 WHERE identifier=$2", servers, ctx.author.id)
            await conn.execute(
                "UPDATE data SET welcome=$1, goodbye=$2, loggingplus=$3 WHERE guild=$4", None, None, False, guild
            )
            await conn.execute("DELETE FROM snippet WHERE guild=$1", guild)
        await ctx.send(
            embed=discord.Embed(description="That server no longer has premium.", colour=self.bot.primary_colour)
        )


def setup(bot):
    bot.add_cog(Premium(bot))

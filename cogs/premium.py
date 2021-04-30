import logging

from discord.ext import commands

from classes.embed import Embed, ErrorEmbed
from utils import checks, tools
from utils.converters import GuildConverter

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
        embed = Embed(
            title="Premium",
            description="Purchasing premium is the best way you can show support to us. As hosting this bot for all "
            "the servers and users costs much money, your donation will certainly help us a lot in keeping the bot "
            "running. You will also get access to the premium features listed below.",
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
            res = await conn.fetchrow(
                "SELECT identifier FROM premium WHERE $1=any(guild)", ctx.guild.id
            )

        await ctx.send(
            embed=Embed(description=f"This server has premium. Offered by: <@{res[0]}>.")
        )

    @checks.is_patron()
    @commands.command(
        description="View a list of servers you assigned premium to.",
        usage="viewpremium",
        aliases=["premiumlist"],
    )
    async def viewpremium(self, ctx):
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow(
                "SELECT guild FROM premium WHERE identifier=$1", ctx.author.id
            )

        if not res or not res[0]:
            await ctx.send(embed=Embed(description="You have not assigned premium to any server."))
            return

        guilds = []
        for guild_id in res[0]:
            guild = await self.bot.get_guild(guild_id)
            guilds.append(f"{guild.name if guild else 'Unknown server'} `{guild_id}`")

        await ctx.send(embed=Embed(title="Premium Servers", description="\n".join(guilds)))

    @checks.is_patron()
    @commands.command(
        description="Assign premium slot to a server.", usage="premiumassign <server ID>"
    )
    async def premiumassign(self, ctx, *, guild: GuildConverter):
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow(
                "SELECT identifier FROM premium WHERE $1=any(guild)", guild.id
            )

        if res:
            await ctx.send(embed=ErrorEmbed(description="That server already has premium."))
            return

        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow(
                "SELECT array_length(guild, 1) FROM premium WHERE identifier=$1", ctx.author.id
            )

        if res[0] and res[0] >= await tools.get_premium_slots(self.bot, ctx.author.id):
            await ctx.send(
                embed=ErrorEmbed(
                    description="You have reached the maximum number of slots that can be assigned. Please upgrade "
                    "your premium to increase the slots."
                )
            )
            return

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE premium SET guild=array_append(guild, $1) WHERE identifier=$2",
                guild.id,
                ctx.author.id,
            )

        await ctx.send(embed=Embed(description="That server now has premium."))

    @checks.is_patron()
    @commands.command(
        description="Remove premium slot from a server.", usage="premiumremove <server ID>"
    )
    async def premiumremove(self, ctx, *, guild: GuildConverter):
        async with self.bot.pool.acquire() as conn:
            res = await conn.fetchrow(
                "SELECT identifier FROM premium WHERE identifier=$1 AND $2=any(guild)",
                ctx.author.id,
                guild.id,
            )

        if not res:
            await ctx.send(
                embed=ErrorEmbed(description="You did not assign premium to that server.")
            )
            return

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE premium SET guild=array_remove(guild, $1) WHERE identifier=$2",
                guild.id,
                ctx.author.id,
            )

        await tools.remove_premium(self.bot, guild.id)

        await ctx.send(embed=Embed(description="That server no longer has premium."))


def setup(bot):
    bot.add_cog(Premium(bot))

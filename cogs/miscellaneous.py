import asyncio
import discord
from discord.ext import commands


class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command(
        description="Go to sleep.",
        usage="sleep",
    )
    async def sleep(self, ctx):
        async with ctx.channel.typing():
            await asyncio.sleep(5)
            await ctx.send("Slept, done.")


def setup(bot):
    bot.add_cog(Miscellaneous(bot))

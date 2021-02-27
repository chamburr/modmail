import logging

from typing import Optional

import discord

from discord.ext import commands

from classes import channel, converters
from utils import checks

log = logging.getLogger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.uri = f"http://{self.bot.config.http_host}:{self.bot.config.http_port}"

    async def find_guild(self, name):
        return [guild for guild in await self.bot.guilds() if guild.name.lower().count(name.lower()) > 0]

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers with the specified name.",
        usage="findserver <name>",
        hidden=True,
    )
    async def findserver(self, ctx, *, name: str):
        guilds = await self.find_guild(name)
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
            all_pages.append(page.to_dict())
        if len(all_pages) == 1:
            embed = discord.Embed.from_dict(all_pages[0])
            embed.set_footer(text=discord.Embed.Empty)
            await ctx.send(embed=embed)
            return
        msg = await ctx.send(embed=discord.Embed.from_dict(all_pages[0]))
        for reaction in ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]:
            await msg.add_reaction(reaction)
        menus = await self.bot._connection._get("reaction_menus") or []
        menus.append(
            {
                "channel": msg.channel.id,
                "message": msg.id,
                "page": 0,
                "all_pages": all_pages,
                "end": datetime.timestamp(datetime.now()) + 2 * 60,
            }
        )
        await self.bot._connection.redis.set("reaction_menus", orjson.dumps(menus).decode("utf-8"))

    async def get_user_guilds(self, user_id):
        guilds = await self.bot._redis.smembers(f"user:{user_id}")
        return [await self.bot.get_guild(int(guild)) for guild in guilds]

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers the bot shares with the user.",
        usage="sharedservers <user>",
        hidden=True,
    )
    async def sharedservers(self, ctx, *, user: converters.GlobalUser):
        guilds = await self.get_user_guilds(user.id)
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
            all_pages.append(page.to_dict())
        if len(all_pages) == 1:
            embed = discord.Embed.from_dict(all_pages[0])
            embed.set_footer(text=discord.Embed.Empty)
            await ctx.send(embed=embed)
            return
        msg = await ctx.send(embed=discord.Embed.from_dict(all_pages[0]))
        for reaction in ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]:
            await msg.add_reaction(reaction)
        menus = await self.bot._connection._get("reaction_menus") or []
        menus.append(
            {
                "channel": msg.channel.id,
                "message": msg.id,
                "page": 0,
                "all_pages": all_pages,
                "end": datetime.timestamp(datetime.now()) + 2 * 60,
            }
        )
        await self.bot._connection.redis.set("reaction_menus", orjson.dumps(menus).decode("utf-8"))

    async def invite_guild(self, guild_id):
        guild = await self.bot.get_guild(guild_id)
        if not guild:
            return
        try:
            invite = (await guild.invites())[0]
        except (IndexError, discord.Forbidden):
            try:
                invite = await self.bot.http.create_invite((await guild.text_channels())[0].id, max_age=120)
            except discord.Forbidden:
                return
        return invite

    @checks.is_admin()
    @commands.command(
        description="Create an invite to the specified server.",
        usage="createinvite <server ID>",
        hidden=True,
    )
    async def createinvite(self, ctx, *, guild: int):
        invite = await self.invite_guild(guild)
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
                    description=f"Here is the invite link: https://discord.gg/{invite['code']}",
                    colour=self.bot.primary_colour,
                )
            )

    async def get_top_guilds(self, count):
        return sorted(await self.bot.guilds(), key=lambda x: x.member_count, reverse=True)[:count]

    @checks.is_admin()
    @commands.command(
        description="Get the top servers using the bot.",
        aliases=["topguilds"],
        usage="topservers [count]",
        hidden=True,
    )
    async def topservers(self, ctx, *, count: int = 20):
        guilds = await self.get_top_guilds(count)
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
            all_pages.append(page.to_dict())
        if len(all_pages) == 1:
            embed = discord.Embed.from_dict(all_pages[0])
            embed.set_footer(text=discord.Embed.Empty)
            await ctx.send(embed=embed)
            return
        msg = await ctx.send(embed=discord.Embed.from_dict(all_pages[0]))
        for reaction in ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]:
            await msg.add_reaction(reaction)
        menus = await self.bot._connection._get("reaction_menus") or []
        menus.append(
            {
                "channel": msg.channel.id,
                "message": msg.id,
                "page": 0,
                "all_pages": all_pages,
                "end": datetime.timestamp(datetime.now()) + 2 * 60,
            }
        )
        await self.bot._connection.redis.set("reaction_menus", orjson.dumps(menus).decode("utf-8"))

    @checks.is_admin()
    @commands.command(description="Make me say something.", usage="echo [channel] <message>", hidden=True)
    async def echo(self, ctx, channel: Optional[channel.TextChannel], *, content: str):
        channel = channel or ctx.channel
        await ctx.message.delete()
        await channel.send(content, allowed_mentions=discord.AllowedMentions(everyone=False))

    @checks.is_admin()
    @commands.command(description="Stop all clusters.", usage="stop", hidden=True)
    async def stop(self, ctx, *, cluster: int):
        await ctx.send(embed=discord.Embed(description="Stopping...", colour=self.bot.primary_colour))
        await self.bot.session.post(f"{self.uri}/stop")

    @checks.is_admin()
    @commands.command(description="Restart all clusters.", usage="restart", hidden=True)
    async def restart(self, ctx):
        await ctx.send(embed=discord.Embed(description="Rolling a restart...", colour=self.bot.primary_colour))
        await self.bot.session.post(f"{self.uri}/restart")


def setup(bot):
    bot.add_cog(Admin(bot))

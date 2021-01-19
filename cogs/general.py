import logging
import platform
import time

import discord
import psutil

from discord.ext import commands

from utils.paginator import Paginator

log = logging.getLogger(__name__)


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        psutil.cpu_percent()

    @commands.bot_has_permissions(add_reactions=True)
    @commands.command(
        description="Shows the help menu or information for a specific command when specified.",
        usage="help [command]",
        aliases=["h", "commands"],
    )
    async def help(self, ctx, *, command: str = None):
        if command:
            command = self.bot.get_command(command.lower())
            if not command:
                await ctx.send(
                    embed=discord.Embed(
                        description=f"That command does not exist. Use `{ctx.prefix}help` to see all the commands.",
                        colour=self.bot.primary_colour,
                    )
                )
                return
            embed = discord.Embed(title=command.name, description=command.description, colour=self.bot.primary_colour)
            usage = "\n".join([ctx.prefix + x.strip() for x in command.usage.split("\n")])
            embed.add_field(name="Usage", value=f"```{usage}```", inline=False)
            if len(command.aliases) > 1:
                embed.add_field(name="Aliases", value=f"`{'`, `'.join(command.aliases)}`")
            elif len(command.aliases) > 0:
                embed.add_field(name="Alias", value=f"`{command.aliases[0]}`")
            await ctx.send(embed=embed)
            return
        all_pages = []
        page = discord.Embed(
            title=f"{self.bot.user.name} Help Menu",
            description="Thank you for using ModMail! Please direct message me if you wish to contact staff. You can "
            "also invite me to your server with the link below, or join our support server if you need further help."
            "\n\nWe released Wyvor - The best feature rich Discord music bot! Check it out now: https://wyvor.xyz.",
            colour=self.bot.primary_colour,
        )
        page.set_thumbnail(url=self.bot.user.avatar_url)
        page.set_footer(text="Use the reactions to flip pages.")
        page.add_field(name="Invite", value="https://modmail.xyz/invite", inline=False)
        page.add_field(name="Support Server", value="https://discord.gg/wjWJwJB", inline=False)
        all_pages.append(page)
        page = discord.Embed(title=f"{self.bot.user.name} Help Menu", colour=self.bot.primary_colour)
        page.set_thumbnail(url=self.bot.user.avatar_url)
        page.set_footer(text="Use the reactions to flip pages.")
        page.add_field(
            name="About ModMail",
            value="ModMail is a feature-rich Discord bot designed to enable your server members to contact staff "
            "easily. A new channel is created whenever a user messages the bot, and the channel will serve as a shared "
            "inbox for seamless communication between staff and the user.",
            inline=False,
        )
        page.add_field(
            name="Getting Started",
            value="Follow these steps to get the bot all ready to serve your server!\n1. Invite the bot with "
            f"[this link](https://modmail.xyz/invite)\n2. Run `{ctx.prefix}setup`, there will be an interactive guide."
            f"\n3. All done! For a full list of commands, see `{ctx.prefix}help`.",
            inline=False,
        )
        all_pages.append(page)
        for _, cog_name in enumerate(self.bot.cogs):
            if cog_name in ["Owner", "Admin"]:
                continue
            cog = self.bot.get_cog(cog_name)
            cog_commands = cog.get_commands()
            if len(cog_commands) == 0:
                continue
            page = discord.Embed(
                title=cog_name,
                description=f"My prefix is `{ctx.prefix}`. Use `{ctx.prefix}"
                "help <command>` for more information on a command.",
                colour=self.bot.primary_colour,
            )
            page.set_author(name=f"{self.bot.user.name} Help Menu", icon_url=self.bot.user.avatar_url)
            page.set_thumbnail(url=self.bot.user.avatar_url)
            page.set_footer(text="Use the reactions to flip pages.")
            for cmd in cog_commands:
                if cmd.hidden is False:
                    page.add_field(name=cmd.name, value=cmd.description, inline=False)
            all_pages.append(page)
        paginator = Paginator(length=1, entries=all_pages, use_defaults=True, embed=True, timeout=120)
        await paginator.start(ctx)

    @commands.command(description="Pong! Get my latency.", usage="ping")
    async def ping(self, ctx):
        start = time.time()
        msg = await ctx.send(embed=discord.Embed(description="Checking latency...", colour=self.bot.primary_colour))
        await msg.edit(
            embed=discord.Embed(
                title="Pong!",
                description=f"Gateway latency: {round(self.bot.latency * 1000, 2)}ms.\n"
                f"HTTP API latency: {round((time.time() - start) * 1000, 2)}ms.",
                colour=self.bot.primary_colour,
            )
        )

    def get_bot_uptime(self, *, brief=False):
        hours, remainder = divmod(int(self.bot.uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        if not brief:
            if days:
                fmt = "{d} days, {h} hours, {m} minutes, and {s} seconds"
            else:
                fmt = "{h} hours, {m} minutes, and {s} seconds"
        else:
            fmt = "{h}h {m}m {s}s"
            if days:
                fmt = "{d}d " + fmt
        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    @commands.command(
        description="See some super cool statistics about me.",
        usage="stats",
        aliases=["statistics", "info"],
    )
    async def stats(self, ctx):
        guilds = sum(await self.bot.comm.handler("guild_count", self.bot.cluster_count))
        channels = sum(await self.bot.comm.handler("channel_count", self.bot.cluster_count))
        users = sum(await self.bot.comm.handler("user_count", self.bot.cluster_count))

        embed = discord.Embed(title=f"{self.bot.user.name} Statistics", colour=self.bot.primary_colour)
        embed.add_field(name="Owner", value="CHamburr#2591")
        embed.add_field(name="Bot Version", value=self.bot.version)
        embed.add_field(name="Uptime", value=self.get_bot_uptime(brief=True))
        embed.add_field(name="Clusters", value=f"{self.bot.cluster}/{self.bot.cluster_count}")
        if ctx.guild:
            embed.add_field(name="Shards", value=f"{ctx.guild.shard_id + 1}/{self.bot.shard_count}")
        else:
            embed.add_field(name="Shards", value=f"{self.bot.shard_count}")
        embed.add_field(name="Servers", value=str(guilds))
        embed.add_field(name="Channels", value=str(channels))
        embed.add_field(name="Users", value=str(users))
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent(interval=None)}%")
        embed.add_field(name="RAM Usage", value=f"{psutil.virtual_memory().percent}%")
        embed.add_field(name="Python Version", value=platform.python_version())
        embed.add_field(name="discord.py Version", value=discord.__version__)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.set_footer(
            text="Made with ❤ using discord.py",
            icon_url="https://www.python.org/static/opengraph-icon-200x200.png",
        )
        await ctx.send(embed=embed)

    @commands.command(
        description="See the amazing stuff we have partnered with.",
        usage="partners",
        aliases=["partner"],
    )
    async def partners(self, ctx):
        all_pages = []
        page = discord.Embed(
            title="Wyvor",
            description="The best feature-rich Discord music bot. Take control over your music with an intuitive "
            "dashboard, custom effects and more!",
            colour=self.bot.primary_colour,
        )
        page.add_field(name="Link", value="https://wyvor.xyz")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/avatars/628563240187723786/06a8639ec4e75387c26de267cc277df1.png"
        )
        all_pages.append(page)
        page = discord.Embed(
            title="Discord Templates",
            description="Discord Templates is the place for you to discover a huge variety of Discord server templates "
            "for all purposes.",
            colour=self.bot.primary_colour,
        )
        page.add_field(name="Link", value="https://discordtemplates.me")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/696179394057732237/cf54e042456638eba2ea5abddfc7910e.png"
        )
        all_pages.append(page)
        page = discord.Embed(
            title="Call of Duty Mobile",
            description="The Activision-supported, community-run discord for the Call of Duty: Mobile Community.",
            colour=self.bot.primary_colour,
        )
        page.add_field(name="Link", value="https://discord.gg/codmobile")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/619762818266431547/a_cce3e6b3b6e64dcf7bbb6fa92c9fc4e6.gif"
        )
        all_pages.append(page)
        page = discord.Embed(
            title="Car Crushers Official Discord",
            description="Official Discord server for the Roblox game, Car Crushers 2. Where you can have both on and "
            "off topic discussions about the game or anything in general with our community of active and friendly "
            "members!",
            colour=self.bot.primary_colour,
        )
        page.add_field(name="Link", value="https://discord.gg/CUkKzGr")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/242263977986359297/a_ff1c6cf6b1b68cfe94d04cb1936e2602.gif"
        )
        all_pages.append(page)
        page = discord.Embed(
            title="Eden of Gaming",
            description="Eden of Gaming is a global gaming community that aims to share knowledge and build "
            "relationships between members and fellow global gaming communities.",
            colour=self.bot.primary_colour,
        )
        page.add_field(name="Link", value="https://discord.gg/edenofgaming")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/457151179072339978/a_6b2bf427b3f07f209386dcf85ea94a9a.gif"
        )
        all_pages.append(page)
        page = discord.Embed(
            title="Homework Help",
            description="Got assignments? Need help? Then come join Discord's premier hub for students, scholars, "
            "professionals, and hobbyists interested in discussions, challenges, as well as news, views, and reviews "
            "that runs the gamut of academic disciplines.",
            colour=self.bot.primary_colour,
        )
        page.add_field(name="Link", value="https://discord.gg/homework")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/238956364729155585/468ac0a7dc84db45d018e0c442fe8447.png"
        )
        all_pages.append(page)
        page = discord.Embed(
            title="Otzdarva's Dungeon",
            description="Otzdarva's Dungeon is a community for the Dead by Daylight streamer Otzdarva, also known for "
            "being a PUBG and Dark Souls YouTuber in the past.",
            colour=self.bot.primary_colour,
        )
        page.add_field(name="Link", value="https://discord.gg/otzdarva")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/227900298549657601/a_74313704119f88dc252e9b0b98c3ab25.gif"
        )
        all_pages.append(page)
        page = discord.Embed(
            title="DOOM",
            description="Hell’s armies have invaded Earth. Become the Slayer in an epic single-player campaign to "
            "conquer demons across dimensions and stop the final destruction of humanity. The only thing they fear... "
            "is you. RAZE HELL in DOOM Eternal!",
            colour=self.bot.primary_colour,
        )
        page.add_field(name="Link", value="https://discord.gg/doom")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/162891400684371968/a_4363040f917b4920a2e78da1e302d9dc.gif"
        )
        all_pages.append(page)
        page = discord.Embed(
            title="Sea of Thieves",
            description="One of the longest running and largest community-run Sea of Thieves Discord servers. A great "
            "and most of all welcoming place to chat about Sea of Thieves and maybe find a few crew mates along the "
            "way.",
            colour=self.bot.primary_colour,
        )
        page.add_field(name="Link", value="https://discord.gg/seaofthievescommunity")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/209815380946845697/a_04c8ae80dce6e6ef1e3d574dca61b4a2.png"
        )
        all_pages.append(page)
        page = discord.Embed(
            title="Underlords",
            description="Underlords Discord server acts as a secondary platform to r/Underlords where users can have "
            "casual chit-chat, give suggestions, share tactics and discuss everything related to Underlords.",
            colour=self.bot.primary_colour,
        )
        page.add_field(name="Link", value="https://discord.gg/underlords")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/580534040692654101/a_0a6f7616c7d9b98f740809dbea272967.gif"
        )
        all_pages.append(page)
        page = discord.Embed(
            title="CH's amburr",
            description="CH's amburr is my personal community server. It is a fun and friendly place where you can "
            "talk about everything cool.",
            colour=self.bot.primary_colour,
        )
        page.add_field(name="Link", value="https://discord.gg/TYe3U4w")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/447732123340767232/5a1064a156540e36e22a38abc527c737.png"
        )
        all_pages.append(page)
        page = discord.Embed(
            title="Member Count",
            description="Member Count is another bot that I am actively developing on. It shows stats on your server "
            "using channel names.",
            colour=self.bot.primary_colour,
        )
        page.add_field(name="Link", value="https://discordbots.org/bot/membercount")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/496964682972659712/0b61c5cb7b9ace8f8f5e2fef37cacb5b.png"
        )
        all_pages.append(page)
        for embed in all_pages:
            embed.set_author(name=f"{self.bot.user.name} partners", icon_url=self.bot.user.avatar_url)
            embed.set_footer(text="Use the reactions to flip pages.")
        paginator = Paginator(length=1, entries=all_pages, use_defaults=True, embed=True, timeout=120)
        await paginator.start(ctx)

    @commands.command(description="Get a link to invite me.", usage="invite")
    async def invite(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                title="Invite Link",
                description="https://modmail.xyz/invite",
                colour=self.bot.primary_colour,
            )
        )

    @commands.command(description="Get a link to my support server.", usage="support", aliases=["server"])
    async def support(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                title="Support Server",
                description="https://discord.gg/wjWJwJB",
                colour=self.bot.primary_colour,
            )
        )

    @commands.command(description="Get the link to ModMail's website.", usage="website")
    async def website(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                title="Website",
                description="https://modmail.xyz",
                colour=self.bot.primary_colour,
            )
        )

    @commands.command(description="Get the link to ModMail's GitHub repository.", usage="source", aliases=["github"])
    async def source(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                title="GitHub Repository",
                description="https://github.com/chamburr/modmail",
                colour=self.bot.primary_colour,
            )
        )


def setup(bot):
    bot.add_cog(General(bot))

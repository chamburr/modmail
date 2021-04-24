import logging
import platform
import time

from datetime import datetime

import distro
import psutil

from discord.ext import commands

from classes.embed import Embed
from utils import checks, tools

log = logging.getLogger(__name__)


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.bot_has_permissions(add_reactions=True)
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
                    embed=Embed(
                        description=f"That command does not exist. Use `{ctx.prefix}help` to see all the commands.",
                    )
                )
                return

            embed = Embed(title=command.name, description=command.description)
            usage = "\n".join([ctx.prefix + x.strip() for x in command.usage.split("\n")])
            embed.add_field(name="Usage", value=f"```{usage}```", inline=False)

            if len(command.aliases) > 1:
                embed.add_field(name="Aliases", value=f"`{'`, `'.join(command.aliases)}`")
            elif len(command.aliases) > 0:
                embed.add_field(name="Alias", value=f"`{command.aliases[0]}`")

            await ctx.send(embed=embed)
            return

        bot_user = await self.bot.real_user()

        all_pages = []

        page = Embed(
            title=f"{bot_user.name} Help Menu",
            description="Thank you for using ModMail! Please direct message me if you wish to contact staff. You can "
            "also invite me to your server with the link below, or join our support server if you need further help.\n"
            f"\nDon't forget to check out our partners with the `{ctx.prefix}partners` command!",
        )
        page.set_thumbnail(url=bot_user.avatar_url)
        page.set_footer(text="Use the reactions to flip pages.")
        page.add_field(name="Invite", value="https://modmail.xyz/invite", inline=False)
        page.add_field(name="Support Server", value="https://discord.gg/wjWJwJB", inline=False)
        all_pages.append(page)

        page = Embed(title=f"{bot_user.name} Help Menu")
        page.set_thumbnail(url=bot_user.avatar_url)
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

        for cog_name in self.bot.cogs:
            if cog_name in ["Owner", "Admin"]:
                continue

            cog = self.bot.get_cog(cog_name)
            cog_commands = cog.get_commands()

            if len(cog_commands) == 0:
                continue

            page = Embed(
                title=cog_name,
                description=f"My prefix is `{ctx.prefix}`. Use `{ctx.prefix}help <command>` for more information on a "
                "command.",
            )

            page.set_author(name=f"{bot_user.name} Help Menu", icon_url=bot_user.avatar_url)
            page.set_thumbnail(url=bot_user.avatar_url)
            page.set_footer(text="Use the reactions to flip pages.")

            for cmd in cog_commands:
                page.add_field(name=cmd.name, value=cmd.description, inline=False)

            all_pages.append(page)

        for page in range(len(all_pages)):
            all_pages[page].set_footer(text=f"Use the reactions to flip pages. (Page {page + 1}/{len(all_pages)})")

        await tools.create_paginator(self.bot, ctx, all_pages)

    @commands.command(description="Pong! Get my latency.", usage="ping")
    async def ping(self, ctx):
        start = time.time()
        shard = ctx.guild.shard_id if ctx.guild else 0

        msg = await ctx.send(embed=Embed(description="Checking latency..."))

        await msg.edit(
            embed=Embed(
                title="Pong!",
                description=f"Gateway latency: {round((await self.bot.statuses())[shard].latency, 2)}ms.\n"
                f"HTTP API latency: {round((time.time() - start) * 1000, 2)}ms.",
            )
        )

    @commands.command(
        description="See some super cool statistics about me.",
        usage="stats",
        aliases=["statistics", "info"],
    )
    async def stats(self, ctx):
        total_seconds = int((datetime.utcnow() - await self.bot.started()).total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        bot_user = await self.bot.real_user()

        embed = Embed(
            title=f"{bot_user.name} Statistics",
            description="Visit the bot status page [here](https://status.modmail.xyz) for more information.",
        )
        embed.add_field(name="Owner", value="CHamburr#2591")
        embed.add_field(name="Bot Version", value=self.bot.version)
        if days:
            embed.add_field(name="Uptime", value=f"{days}d {hours}h {minutes}m {seconds}s")
        else:
            embed.add_field(name="Uptime", value=f"{hours}h {minutes}m {seconds}s")
        embed.add_field(name="Clusters", value=self.bot.cluster_count)
        if ctx.guild:
            embed.add_field(name="Shards", value=f"{ctx.guild.shard_id + 1}/{await self.bot.shard_count()}")
        else:
            embed.add_field(name="Shards", value=f"0/{await self.bot.shard_count()}")
        embed.add_field(name="Servers", value=str(await self.bot.state.scard("guild_keys")))
        embed.add_field(name="Channels", value=str(await self.bot.state.scard("channel_keys")))
        embed.add_field(name="Users", value=str(await self.bot.state.scard("user_keys")))
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent(interval=None)}%")
        embed.add_field(name="RAM Usage", value=f"{psutil.virtual_memory().percent}%")
        embed.add_field(name="Platform", value=" ".join(distro.linux_distribution()[:2]))
        embed.add_field(name="Python Version", value=platform.python_version())
        embed.set_thumbnail(url=bot_user.avatar_url)

        await ctx.send(embed=embed)

    @checks.bot_has_permissions(add_reactions=True)
    @commands.command(description="See the amazing stuff we have partnered with.", usage="partners")
    async def partners(self, ctx):
        all_pages = []

        page = Embed(
            title="Discord Templates",
            description="Discord Templates is the place for you to discover a huge variety of Discord server templates "
            "for all purposes.",
        )
        page.add_field(name="Link", value="https://discordtemplates.me")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/696179394057732237/cf54e042456638eba2ea5abddfc7910e.png"
        )
        all_pages.append(page)

        page = Embed(
            title="Call of Duty Mobile",
            description="The Activision-supported, community-run discord for the Call of Duty: Mobile Community.",
        )
        page.add_field(name="Link", value="https://discord.gg/codmobile")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/619762818266431547/a_cce3e6b3b6e64dcf7bbb6fa92c9fc4e6.gif"
        )
        all_pages.append(page)

        page = Embed(
            title="Eden of Gaming",
            description="Eden of Gaming is a global gaming community that aims to share knowledge and build "
            "relationships between members and fellow global gaming communities.",
        )
        page.add_field(name="Link", value="https://discord.gg/edenofgaming")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/457151179072339978/a_6b2bf427b3f07f209386dcf85ea94a9a.gif"
        )
        all_pages.append(page)

        page = Embed(
            title="Homework Help",
            description="Got assignments? Need help? Then come join Discord's premier hub for students, scholars, "
            "professionals, and hobbyists interested in discussions, challenges, as well as news, views, and reviews "
            "that runs the gamut of academic disciplines.",
        )
        page.add_field(name="Link", value="https://discord.gg/homework")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/238956364729155585/468ac0a7dc84db45d018e0c442fe8447.png"
        )
        all_pages.append(page)

        page = Embed(
            title="Otzdarva's Dungeon",
            description="Otzdarva's Dungeon is a community for the Dead by Daylight streamer Otzdarva, also known for "
            "being a PUBG and Dark Souls YouTuber in the past.",
        )
        page.add_field(name="Link", value="https://discord.gg/otzdarva")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/227900298549657601/a_74313704119f88dc252e9b0b98c3ab25.gif"
        )
        all_pages.append(page)

        page = Embed(
            title="DOOM",
            description="Hell’s armies have invaded Earth. Become the Slayer in an epic single-player campaign to "
            "conquer demons across dimensions and stop the final destruction of humanity. The only thing they fear... "
            "is you. RAZE HELL in DOOM Eternal!",
        )
        page.add_field(name="Link", value="https://discord.gg/doom")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/162891400684371968/a_4363040f917b4920a2e78da1e302d9dc.gif"
        )
        all_pages.append(page)

        page = Embed(
            title="Sea of Thieves",
            description="One of the longest running and largest community-run Sea of Thieves Discord servers. A great "
            "and most of all welcoming place to chat about Sea of Thieves and maybe find a few crew mates along the "
            "way.",
        )
        page.add_field(name="Link", value="https://discord.gg/seaofthievescommunity")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/209815380946845697/a_04c8ae80dce6e6ef1e3d574dca61b4a2.png"
        )
        all_pages.append(page)

        page = Embed(
            title="Underlords",
            description="Underlords Discord server acts as a secondary platform to r/Underlords where users can have "
            "casual chit-chat, give suggestions, share tactics and discuss everything related to Underlords.",
        )
        page.add_field(name="Link", value="https://discord.gg/underlords")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/580534040692654101/a_0a6f7616c7d9b98f740809dbea272967.gif"
        )
        all_pages.append(page)

        page = Embed(
            title="CH's amburr",
            description="CH's amburr is my personal community server. It is a fun and friendly place where you can "
            "talk about everything cool.",
        )
        page.add_field(name="Link", value="https://discord.gg/TYe3U4w")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/447732123340767232/5a1064a156540e36e22a38abc527c737.png"
        )
        all_pages.append(page)

        page = Embed(
            title="Member Count",
            description="Member Count is another bot that I am actively developing on. It shows stats on your server "
            "using channel names.",
        )
        page.add_field(name="Link", value="https://discordbots.org/bot/membercount")
        page.set_thumbnail(
            url="https://cdn.discordapp.com/icons/496964682972659712/0b61c5cb7b9ace8f8f5e2fef37cacb5b.png"
        )
        all_pages.append(page)

        for page in range(len(all_pages)):
            bot_user = await self.bot.real_user()
            all_pages[page].set_author(name=f"{bot_user.name} partners", icon_url=bot_user.avatar_url)
            all_pages[page].set_footer(text=f"Use the reactions to flip pages. (Page {page + 1}/{len(all_pages)})")

        await tools.create_paginator(self.bot, ctx, all_pages)

    @commands.command(description="Get a link to invite me.", usage="invite")
    async def invite(self, ctx):
        await ctx.send(
            embed=Embed(
                title="Invite Link",
                description="https://modmail.xyz/invite",
            )
        )

    @commands.command(description="Get a link to my support server.", usage="support", aliases=["server"])
    async def support(self, ctx):
        await ctx.send(
            embed=Embed(
                title="Support Server",
                description="https://discord.gg/wjWJwJB",
            )
        )

    @commands.command(description="Get the link to ModMail's website.", usage="website")
    async def website(self, ctx):
        await ctx.send(
            embed=Embed(
                title="Website",
                description="https://modmail.xyz",
            )
        )

    @commands.command(description="Get the link to ModMail's GitHub repository.", usage="source", aliases=["github"])
    async def source(self, ctx):
        await ctx.send(
            embed=Embed(
                title="GitHub Repository",
                description="https://github.com/chamburr/modmail",
            )
        )


def setup(bot):
    bot.add_cog(General(bot))

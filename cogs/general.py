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
                    Embed(
                        f"That command does not exist. Use `{ctx.prefix}help` to see all the "
                        "commands.",
                    )
                )
                return

            embed = Embed(command.name, command.description)
            usage = "\n".join([ctx.prefix + x.strip() for x in command.usage.split("\n")])
            embed.add_field("Usage", f"```{usage}```", False)

            if len(command.aliases) > 1:
                embed.add_field("Aliases", f"`{'`, `'.join(command.aliases)}`")
            elif len(command.aliases) > 0:
                embed.add_field("Alias", f"`{command.aliases[0]}`")

            await ctx.send(embed)
            return

        bot_user = await self.bot.real_user()

        all_pages = []

        page = Embed(
            f"{bot_user.name} Help Menu",
            "Thank you for using ModMail! Please direct message me if you wish to contact staff. "
            "You can also invite me to your server with the link below, or join our support server "
            "if you need further help.",
        )
        page.set_thumbnail(bot_user.avatar_url)
        page.set_footer("Use the reactions to flip pages.")
        page.add_field("Invite", "https://modmail.xyz/invite", False)
        page.add_field("Support Server", "https://discord.gg/wjWJwJB", False)
        all_pages.append(page)

        page = Embed(title=f"{bot_user.name} Help Menu")
        page.set_thumbnail(bot_user.avatar_url)
        page.set_footer("Use the reactions to flip pages.")
        page.add_field(
            "About ModMail",
            "ModMail is a feature-rich Discord bot designed to enable your server members to "
            "contact staff easily. A new channel is created whenever a user messages the bot, and "
            "the channel will serve as a shared inbox for seamless communication between staff and "
            "the user.",
            False,
        )
        page.add_field(
            "Getting Started",
            "Follow these steps to get the bot all ready to serve your server!\n1. Invite the bot "
            f"with [this link](https://modmail.xyz/invite)\n2. Run `{ctx.prefix}setup`.\n3. All "
            f"done! For the full list of commands, see `{ctx.prefix}help`.",
            False,
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
                cog_name,
                f"My prefix is `{ctx.prefix}`. Use `{ctx.prefix}help <command>` for more "
                "information on a command.",
            )

            page.set_author(f"{bot_user.name} Help Menu", bot_user.avatar_url)
            page.set_thumbnail(bot_user.avatar_url)
            page.set_footer("Use the reactions to flip pages.")

            for cmd in cog_commands:
                page.add_field(cmd.name, cmd.description, False)

            all_pages.append(page)

        for page in range(len(all_pages)):
            all_pages[page].set_footer(
                f"Use the reactions to flip pages. (Page {page + 1}/{len(all_pages)})"
            )

        await tools.create_paginator(self.bot, ctx, all_pages)

    @commands.command(description="Pong! Get my latency.", usage="ping")
    async def ping(self, ctx):
        start = time.time()
        shard = ctx.guild.shard_id if ctx.guild else 0

        msg = await ctx.send(Embed("Checking latency..."))

        await msg.edit(
            Embed(
                "Pong!",
                f"Gateway latency: {round((await self.bot.statuses())[shard].latency, 2)}ms.\n"
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
            f"{bot_user.name} Statistics",
            "Visit the bot status page [here](https://modmail.xyz/status) for more information.",
        )
        embed.add_field("Owner", "CHamburr#2591")
        embed.add_field("Bot Version", self.bot.version)
        if days:
            embed.add_field("Uptime", f"{days}d {hours}h {minutes}m {seconds}s")
        else:
            embed.add_field("Uptime", f"{hours}h {minutes}m {seconds}s")
        embed.add_field("Clusters", self.bot.cluster_count)
        if ctx.guild:
            embed.add_field("Shards", f"{ctx.guild.shard_id + 1}/{await self.bot.shard_count()}")
        else:
            embed.add_field("Shards", f"0/{await self.bot.shard_count()}")
        embed.add_field("Servers", str(await self.bot.state.scard("guild_keys")))
        embed.add_field("Channels", str(await self.bot.state.scard("channel_keys")))
        embed.add_field("Users", str(await self.bot.state.scard("user_keys")))
        embed.add_field("CPU Usage", f"{psutil.cpu_percent(interval=None)}%")
        embed.add_field("RAM Usage", f"{psutil.virtual_memory().percent}%")
        embed.add_field("Platform", " ".join(distro.linux_distribution()[:2]))
        embed.add_field("Python Version", platform.python_version())
        embed.set_thumbnail(bot_user.avatar_url)

        await ctx.send(embed)

    @commands.command(description="See the amazing stuff we have partnered with.", usage="partners")
    async def partners(self, ctx):
        await ctx.send(Embed("Partners", "https://modmail.xyz/partners"))

    @commands.command(description="Get a link to invite me.", usage="invite")
    async def invite(self, ctx):
        await ctx.send(Embed("Invite Link", "https://modmail.xyz/invite"))

    @commands.command(
        description="Get a link to my support server.", usage="support", aliases=["server"]
    )
    async def support(self, ctx):
        await ctx.send(Embed("Support Server", "https://discord.gg/wjWJwJB"))

    @commands.command(description="Get the link to ModMail's website.", usage="website")
    async def website(self, ctx):
        await ctx.send(Embed("Website", "https://modmail.xyz"))

    @commands.command(
        description="Get the link to ModMail's GitHub repository.",
        usage="source",
        aliases=["github"],
    )
    async def source(self, ctx):
        await ctx.send(Embed("GitHub Repository", "https://github.com/chamburr/modmail"))


def setup(bot):
    bot.add_cog(General(bot))

import psutil
import platform
import discord
from discord.ext import commands
from utils.paginator import Paginator


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(add_reactions=True)
    @commands.command(
        description="Shows the help menu of all commands, or a specific command when specified.",
        usage="help [command]",
        aliases=["h", "commands"],
    )
    async def help(self, ctx, *, command: str = None):
        if command:
            command = self.bot.get_command(command.lower())
            if not command:
                return await ctx.send(
                    embed=discord.Embed(
                        description=f"That command does not exist. Use `{ctx.prefix}help` to see all the commands.",
                        color=self.bot.primary_colour,
                    )
                )
            embed = discord.Embed(
                title=command.name,
                description=command.description,
                color=self.bot.primary_colour,
            )
            usage = "\n".join(
                [ctx.prefix + x.strip() for x in command.usage.split("\n")]
            )
            embed.add_field(name="Usage", value=f"```{usage}```", inline=False)
            if len(command.aliases) > 1:
                embed.add_field(
                    name="Aliases", value=f"`{'`, `'.join(command.aliases)}`"
                )
            elif len(command.aliases) > 0:
                embed.add_field(name="Alias", value=f"`{command.aliases[0]}`")
            await ctx.send(embed=embed)
            return
        all_pages = []
        page = discord.Embed(
            title=f"{self.bot.user.name} Help Menu",
            description='*"Finally a ModMail bot made for everyone."*\n\nThank you for using ModMail! If you are an '
            "ordinary user and wants to contact the staff, all that you need to do is to direct message me. You can "
            "also invite me to your server with the link below, or join our support server should you need further "
            f"help.\n\nDon't forget to check out our partners with the `{ctx.prefix}partners` command!",
            color=self.bot.primary_colour,
        )
        page.set_thumbnail(url=self.bot.user.avatar_url)
        page.set_footer(text="Use the reactions to flip pages.")
        page.add_field(
            name="Invite",
            value=f"https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}"
            "&permissions=268823640&scope=bot",
            inline=False,
        )
        page.add_field(
            name="Support Server", value="https://discord.gg/wjWJwJB", inline=False
        )
        all_pages.append(page)
        page = discord.Embed(
            title=f"{self.bot.user.name} Help Menu", color=self.bot.primary_colour
        )
        page.set_thumbnail(url=self.bot.user.avatar_url)
        page.set_footer(text="Use the reactions to flip pages.")
        page.add_field(
            name="About ModMail",
            value="ModMail is designed to enable your server members to contact staff easily. When a user sends a "
            "direct message to the bot, a new channel is created in your server. Messages sent by the user will be "
            "displayed there and sending a message in that channel will also forward it to that user. This bot is "
            "different from the others as it is the one and only public ModMail bot. This means that it is ensured "
            "to be hosted 24/7 without you having to pay extra hosting fees.",
            inline=False,
        )
        page.add_field(
            name="Getting Started",
            value="Follow these steps to get the bot all ready to serve your server!\n\n1. Invite the bot with the "
            "link below.\n2. Run `=setup`, there will be an interactive guide.\n3. Done! For a full list of commands, "
            "see `=help`.",
            inline=False,
        )
        all_pages.append(page)
        for index, cog_name in enumerate(self.bot.cogs):
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
                color=self.bot.primary_colour,
            )
            page.set_author(
                name=f"{self.bot.user.name} Help Menu",
                icon_url=self.bot.user.avatar_url,
            )
            page.set_thumbnail(url=self.bot.user.avatar_url)
            page.set_footer(text="Use the reactions to flip pages.")
            for cmd in cog_commands:
                if cmd.hidden is False:
                    page.add_field(name=cmd.name, value=cmd.description, inline=False)
            all_pages.append(page)
        paginator = Paginator(
            length=1, entries=all_pages, use_defaults=True, embed=True, timeout=120
        )
        await paginator.start(ctx)

    @commands.command(description="Pong! Get my latency.", usage="ping")
    async def ping(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                title="Pong!",
                description=f"My current latency is {round(self.bot.latency * 1000, 2)}ms.",
                color=self.bot.primary_colour,
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
        guilds = 0
        channels = 0
        total_members = 0
        total_online = 0

        for guild in self.bot.guilds:
            guilds += 1
            for _ in guild.channels:
                channels += 1

        offline = discord.Status.offline
        for member in self.bot.get_all_members():
            total_members += 1
            if member.status is not offline:
                total_online += 1

        embed = discord.Embed(
            title=f"{self.bot.user.name} Statistics", color=self.bot.primary_colour
        )
        embed.add_field(name="Owner", value="CHamburr#2591")
        embed.add_field(name="Bot Version", value=self.bot.version)
        embed.add_field(name="Uptime", value=self.get_bot_uptime(brief=True))
        embed.add_field(
            name="Shards",
            value=f"{f'{ctx.guild.shard_id}/' if ctx.guild else ''}{self.bot.shard_count}",
        )
        embed.add_field(name="Servers", value=str(guilds))
        embed.add_field(name="Channels", value=str(channels))
        embed.add_field(name="Users", value=str(total_members))
        embed.add_field(name="Online Users", value=str(total_online))
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%")
        embed.add_field(name="RAM Usage", value=f"{psutil.virtual_memory().percent}%")
        embed.add_field(name="Python Version", value=platform.python_version())
        embed.add_field(name="discord.py Version", value=discord.__version__)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.set_footer(
            text=f"Made with ❤ using discord.py",
            icon_url="https://www.python.org/static/opengraph-icon-200x200.png",
        )
        await ctx.send(embed=embed)

    @commands.command(
        description="Get the link to vote for ModMail on DiscordBotList.", usage="vote"
    )
    async def vote(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                title="Vote for ModMail",
                description=f"Please vote for me here: https://discordbots.org/bot/575252669443211264. Thank you!",
                color=self.bot.primary_colour,
            )
        )

    @commands.command(description="Get a link to invite me.", usage="invite")
    async def invite(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                title="Invite Me!",
                description=f"https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}"
                "&permissions=268823640&scope=bot",
                color=self.bot.primary_colour,
            )
        )

    @commands.command(
        description="Get a link to my support server.",
        usage="support",
        aliases=["server"],
    )
    async def support(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                title="Support Server",
                description="You can join the support server with this link: https://discord.gg/wjWJwJB",
                color=self.bot.primary_colour,
            )
        )


def setup(bot):
    bot.add_cog(General(bot))

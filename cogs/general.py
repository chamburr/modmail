import psutil
import platform
import datetime
import discord
from discord.ext import commands
from utils.paginator import Paginator


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
            usage = "\n".join([ctx.prefix + x.strip() for x in command.usage.split('\n')])
            embed.add_field(name="Usage", value=f"```{usage}```", inline=False)
            if len(command.aliases) > 1:
                embed.add_field(name="Aliases", value=f"`{'`, `'.join(command.aliases)}`")
            elif len(command.aliases) > 0:
                embed.add_field(name="Alias", value=f"`{command.aliases[0]}`")
            await ctx.send(embed=embed)
            return

        all_pages = []
        for index, cog_name in enumerate(self.bot.cogs):
            if cog_name in ["Owner"]:
                continue
            cog = self.bot.get_cog(cog_name)
            cog_commands = cog.get_commands()
            if len(cog_commands) == 0:
                continue
            page = discord.Embed(
                title=f"**{cog_name}**\n",
                description=f"My prefix is `{ctx.prefix}`. Use `{ctx.prefix}"
                "help <command>` for more information on a command.",
                color=self.bot.primary_colour,
            )
            page.set_author(name=f"{self.bot.user.name} Help Menu", icon_url=self.bot.user.avatar_url)
            page.set_thumbnail(url=self.bot.user.avatar_url)
            page.set_footer(text="Use the reactions to flip pages.")
            for cmd in cog_commands:
                page.add_field(name=cmd.name, value=cmd.description, inline=False)
            all_pages.append(page)

        paginator = Paginator(
            length=1,
            entries=all_pages,
            use_defaults=True,
            embed=True,
            timeout=120,
        )
        await paginator.start(ctx)

    @commands.command(
        description="Pong! Get my latency.",
        usgae="ping",
    )
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
                fmt = '{d} days, {h} hours, {m} minutes, and {s} seconds'
            else:
                fmt = '{h} hours, {m} minutes, and {s} seconds'
        else:
            fmt = '{h}h {m}m {s}s'
            if days:
                fmt = '{d}d ' + fmt
        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    @commands.command(
        description="Get some super cool statistics about me.",
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
            title=f"{self.bot.user.name} Statistics",
            color=self.bot.primary_colour,
        )
        embed.add_field(name="Owner", value="CHamburr#2591")
        embed.add_field(name="Bot Version", value=self.bot.version)
        embed.add_field(name="Uptime", value=self.get_bot_uptime(brief=True))
        embed.add_field(name="Shards", value=f"{f'{ctx.guild.shard_id}/' if ctx.guild else ''}{self.bot.shard_count}")
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
        description="Get a link to invite me.",
        usage="invite",
    )
    async def invite(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                title="Invite Me!",
                description=f"https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}"
                            "&permissions=8&scope=bot",
                color=self.bot.primary_colour,
            )
        )

    @commands.command(
        description="Get a link to my support server.",
        usage="support",
        aliases=["server"],
    )
    async def support(self, ctx):
        await ctx.send("You can join the support server with the following link:\nhttps://discord.gg/TYe3U4w")


def setup(bot):
    bot.add_cog(General(bot))

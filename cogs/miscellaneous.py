import logging

from discord.ext import commands

from classes.embed import Embed
from utils import checks, tools
from utils.converters import MemberConverter

log = logging.getLogger(__name__)


class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Show your permissions or the member specified.",
        usage="permissions [member]",
        aliases=["perms"],
    )
    async def permissions(self, ctx, member: MemberConverter = None):
        if member is None:
            member = ctx.message.member

        permissions = await ctx.channel.permissions_for(member)

        embed = Embed(title="Permission Information")
        embed.add_field("User", str(member), False)
        embed.add_field(
            "Allowed",
            "\n".join([tools.perm_format(name) for name, value in permissions if value]),
        )
        embed.add_field(
            "Denied",
            "\n".join([tools.perm_format(name) for name, value in permissions if not value]),
        )

        await ctx.send(embed)

    @commands.guild_only()
    @commands.command(
        description="Show some information about yourself or the member specified.",
        usage="userinfo [member]",
        aliases=["memberinfo"],
    )
    async def userinfo(self, ctx, *, member: MemberConverter = None):
        if member is None:
            member = ctx.message.member

        roles = [f"<@&{role}>" for role in member._roles]
        if len(roles) == 0:
            roles.append("*No roles*")

        embed = Embed(title="User Information")
        embed.add_field("Name", str(member))
        embed.add_field("ID", member.id)
        embed.add_field("Nickname", member.nick if member.nick else "*Not set*")
        embed.add_field("Avatar", f"[Link]({member.avatar_url_as(static_format='png')})")
        embed.add_field(
            "Joined Server",
            member.joined_at.replace(microsecond=0) if member.joined_at else "Unknown",
        )
        embed.add_field("Account Created", member.created_at.replace(microsecond=0))
        embed.add_field(
            "Roles",
            f"{len(roles)} roles" if len(", ".join(roles)) > 1000 else ", ".join(roles),
        )
        embed.set_thumbnail(member.avatar_url)

        await ctx.send(embed)

    @commands.guild_only()
    @commands.command(
        description="Get some information about this server.",
        usage="serverinfo",
        aliases=["guildinfo"],
    )
    async def serverinfo(self, ctx):
        guild = await self.bot.get_guild(ctx.guild.id)

        embed = Embed(title="Server Information")
        embed.add_field("Name", guild.name)
        embed.add_field("ID", guild.id)
        embed.add_field("Owner", f"<@{guild.owner_id}>" if guild.owner_id else "Unknown")
        embed.add_field(
            "Icon",
            f"[Link]({guild.icon_url_as(static_format='png')})" if guild.icon else "*Not set*",
        )
        embed.add_field("Server Created", guild.created_at.replace(microsecond=0))
        embed.add_field("Members", guild.member_count)
        embed.add_field("Channels", str(len(await guild.channels())))
        embed.add_field("Roles", str(len(await guild.roles())))

        if guild.icon:
            embed.set_thumbnail(guild.icon_url)

        await ctx.send(embed)


def setup(bot):
    bot.add_cog(Miscellaneous(bot))

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
        embed.add_field(name="User", value=str(member), inline=False)
        embed.add_field(
            name="Allowed",
            value="\n".join([tools.perm_format(name) for name, value in permissions if value]),
        )
        embed.add_field(
            name="Denied",
            value="\n".join([tools.perm_format(name) for name, value in permissions if not value]),
        )

        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(
        description="Show some information about yourself or the member specified.",
        usage="userinfo [member]",
        aliases=["memberinfo"],
    )
    async def userinfo(self, ctx, *, member: MemberConverter = None):
        if member is None:
            member = ctx.message.member

        roles = [role.name for role in await member.roles()]

        embed = Embed(title="User Information")
        embed.add_field(name="Name", value=str(member))
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Nickname", value=member.nick if member.nick else "*Not set*")
        embed.add_field(name="Avatar", value=f"[Link]({member.avatar_url_as(static_format='png')})")
        embed.add_field(
            name="Joined Server", value=member.joined_at.replace(microsecond=0) if member.joined_at else "Unknown"
        )
        embed.add_field(name="Account Created", value=member.created_at.replace(microsecond=0))
        embed.add_field(name="Roles", value=f"{len(roles)} roles" if len(", ".join(roles)) > 1000 else ", ".join(roles))
        embed.set_thumbnail(url=member.avatar_url)

        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(description="Get some information about this server.", usage="serverinfo", aliases=["guildinfo"])
    async def serverinfo(self, ctx):
        guild = await self.bot.get_guild(ctx.guild.id)

        embed = Embed(title="Server Information")
        embed.add_field(name="Name", value=guild.name)
        embed.add_field(name="ID", value=guild.id)
        embed.add_field(name="Owner", value=f"<@{guild.owner_id}>" if guild.owner_id else "Unknown")
        embed.add_field(
            name="Icon", value=f"[Link]({guild.icon_url_as(static_format='png')})" if guild.icon else "*Not set*"
        )
        embed.add_field(name="Server Created", value=guild.created_at.replace(microsecond=0))
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Channels", value=str(len(await guild.channels())))
        embed.add_field(name="Roles", value=str(len(await guild.roles())))
        embed.add_field(name="Emojis", value=str(len(await guild.emojis())))

        if guild.icon:
            embed.set_thumbnail(url=guild.icon_url)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Miscellaneous(bot))

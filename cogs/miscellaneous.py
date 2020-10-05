import logging

import discord

from discord.ext import commands

log = logging.getLogger(__name__)


class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Show a member's permission in a channel when specified.",
        usage="permissions [member] [channel]",
        aliases=["perms"],
    )
    async def permissions(self, ctx, member: discord.Member = None, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        if member is None:
            member = ctx.author
        permissions = channel.permissions_for(member)
        embed = discord.Embed(title="Permission Information", colour=self.bot.primary_colour)
        embed.add_field(name="User", value=str(member), inline=False)
        embed.add_field(
            name="Allowed",
            value="\n".join([self.bot.tools.perm_format(name) for name, value in permissions if value]),
        )
        embed.add_field(
            name="Denied",
            value="\n".join([self.bot.tools.perm_format(name) for name, value in permissions if not value]),
        )
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(
        description="Show some information about yourself or the member specified.",
        usage="userinfo [member]",
        aliases=["memberinfo"],
    )
    async def userinfo(self, ctx, *, member: discord.Member = None):
        if member is None:
            member = ctx.author
        roles = [role.name for role in member.roles]
        embed = discord.Embed(title="User Information", colour=self.bot.primary_colour)
        embed.add_field(name="Name", value=str(member))
        embed.add_field(name="ID", value=member.id)
        embed.add_field(
            name="Status", value=str(member.status).title() + (" (mobile)" if member.is_on_mobile() else "")
        )
        embed.add_field(name="Avatar", value=f"[Link]({member.avatar_url_as(static_format='png')})")
        embed.add_field(
            name="Joined Server", value=member.joined_at.replace(microsecond=0) if member.joined_at else "Unknown"
        )
        embed.add_field(name="Account Created", value=member.created_at.replace(microsecond=0))
        embed.add_field(name="Roles", value=f"{len(roles)} roles" if len(", ".join(roles)) > 1000 else ", ".join(roles))
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(
        description="Get some information about this server.",
        usage="serverinfo",
        aliases=["guildinfo"],
    )
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title="Server Information", colour=self.bot.primary_colour)
        embed.add_field(name="Name", value=guild.name)
        embed.add_field(name="ID", value=guild.id)
        embed.add_field(name="Owner", value=str(guild.owner) if guild.owner else "Unknown")
        embed.add_field(
            name="Icon", value=f"[Link]({guild.icon_url_as(static_format='png')})" if guild.icon else "*Not set*"
        )
        embed.add_field(name="Server Created", value=guild.created_at.replace(microsecond=0))
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Channels", value=len(guild.text_channels) + len(guild.voice_channels))
        embed.add_field(name="Roles", value=len(guild.roles))
        embed.add_field(name="Emojis", value=len(guild.emojis))
        if guild.icon:
            embed.set_thumbnail(url=guild.icon_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Miscellaneous(bot))

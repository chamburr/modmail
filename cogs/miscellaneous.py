import discord
from discord.ext import commands

from utils.tools import perm_format


class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def say_permissions(self, ctx, member, channel):
        permissions = channel.permissions_for(member)
        embed = discord.Embed(
            title=f"Permissions for {member.name}#{member.discriminator}", colour=self.bot.primary_colour,
        )
        allowed, denied = [], []
        for name, value in permissions:
            name = perm_format(name)
            if value:
                allowed.append(name)
            else:
                denied.append(name)

        embed.add_field(name="Allowed", value="\n".join(allowed))
        embed.add_field(name="Denied", value="\n".join(denied))
        await ctx.send(embed=embed)

    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Shows a member's permission in a channel when specified.",
        usage="permissions [member] [channel]",
        aliases=["perms"],
    )
    async def permissions(self, ctx, member: discord.Member = None, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        if member is None:
            member = ctx.author
        await self.say_permissions(ctx, member, channel)

    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Shows the bot's permissions in the current or specified channel.",
        usage="botpermissions [channel]",
        aliases=["botperms"],
    )
    async def botpermissions(self, ctx, *, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        member = ctx.guild.me
        await self.say_permissions(ctx, member, channel)

    @commands.guild_only()
    @commands.command(
        description="Shows some information about yourself or the member you specified.",
        usage="userinfo [member]",
        aliases=["whois"],
    )
    async def userinfo(self, ctx, *, member: discord.Member = None):
        if member is None:
            member = ctx.author
        embed = discord.Embed(
            title=f"User Information for {member.name}#{member.discriminator}", colour=self.bot.primary_colour,
        )
        roles = [role.name for role in member.roles]
        embed.add_field(name="Status", value=str(member.status).title())
        embed.add_field(name="On Mobile", value=member.is_on_mobile())
        embed.add_field(name="User ID", value=member.id)
        embed.add_field(name="Avatar", value=f"[Link]({member.avatar_url})")
        embed.add_field(name="Joined Server", value=member.joined_at.replace(microsecond=0))
        embed.add_field(name="Account Created", value=member.created_at.replace(microsecond=0))
        embed.add_field(
            name="Roles", value=f"{len(roles)} roles" if len(", ".join(roles)) > 1000 else ", ".join(roles),
        )
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(
        description="Get some information about this server.", usage="serverinfo", aliases=["guildinfo"],
    )
    async def serverinfo(self, ctx):
        guild = ctx.guild
        roles = [role.name for role in guild.roles]
        embed = discord.Embed(title="Server Information", colour=self.bot.primary_colour)
        embed.add_field(name="Name", value=guild.name)
        embed.add_field(name="ID", value=guild.id)
        embed.add_field(name="Owner", value=f"{guild.owner.name}#{guild.owner.discriminator}")
        embed.add_field(name="Server Created", value=guild.created_at.replace(microsecond=0))
        embed.add_field(
            name="Icon", value=f"[Link]({guild.icon_url})" if guild.icon_url else "None",
        )
        embed.add_field(
            name="Channels", value=str(len(guild.text_channels) + len(guild.voice_channels)),
        )
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Roles", value=str(len(roles)))
        if guild.icon:
            embed.set_thumbnail(url=guild.icon_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Miscellaneous(bot))

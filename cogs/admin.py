import discord
from discord.ext import commands

from utils import checks


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers with the specified name.", usage="findserver <name>", hidden=True,
    )
    async def findserver(self, ctx, *, name: str):
        guilds = []
        for guild in self.bot.guilds:
            if guild.name.lower().count(name.lower()) > 0:
                guilds.append(f"{guild.name} `{guild.id}`")
        if len(guilds) == 0:
            await ctx.send(embed=discord.Embed(description="No such guild was found.", colour=self.bot.error_colour))
        else:
            try:
                await ctx.send(embed=discord.Embed(description="\n".join(guilds), colour=self.bot.primary_colour))
            except discord.HTTPException:
                await ctx.send(
                    embed=discord.Embed(
                        description="The message is too long to be sent.", colour=self.bot.error_colour,
                    )
                )

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers the bot shares with the user.", usage="sharedservers <user>",
    )
    async def sharedservers(self, ctx, *, user):
        try:
            user = await commands.UserConverter().convert(ctx, user)
        except commands.errors.BadArgument:
            return await ctx.send(
                embed=discord.Embed(description="No such user was found.", colour=self.bot.error_colour)
            )
        guilds = [guild for guild in self.bot.guilds if guild.get_member(user.id)]
        guild_list = []
        for guild in guilds:
            entry = f"{guild.name} `{guild.id}`"
            perms = guild.get_member(user.id).guild_permissions
            if guild.owner_id == user.id:
                entry = entry + " (Owner)"
            elif perms.administrator is True:
                entry = entry + " (Admin)"
            elif perms.manage_guild is True or perms.kick_members is True or perms.ban_members is True:
                entry = entry + " (Mod)"
            guild_list.append(entry)
        try:
            await ctx.send(embed=discord.Embed(description="\n".join(guild_list), colour=self.bot.primary_colour))
        except discord.HTTPException:
            await ctx.send(
                embed=discord.Embed(description="The message is too long to be sent.", colour=self.bot.error_colour)
            )

    @checks.is_admin()
    @commands.command(
        description="Create an invite to the specified server.", usage="createinvite <server ID>", hidden=True,
    )
    async def createinvite(self, ctx, *, guild_id: int):
        for guild in self.bot.guilds:
            if guild.id == guild_id:
                try:
                    invite = (await guild.invites())[0]
                    return await ctx.send(
                        embed=discord.Embed(
                            description=f"Found invite created by {invite.inviter.name}: {invite.url}.",
                            colour=self.bot.primary_colour,
                        )
                    )
                except (IndexError, discord.Forbidden):
                    try:
                        invite = (await guild.text_channels[0].create_invite(max_age=120)).url
                        return await ctx.send(
                            embed=discord.Embed(
                                description="Created an invite to the server that will expire in 120 seconds: "
                                f"{invite}.",
                                colour=self.bot.primary_colour,
                            )
                        )
                    except discord.Forbidden:
                        return await ctx.send(
                            embed=discord.Embed(
                                description="No permissions to create an invite link.", colour=self.bot.primary_colour,
                            )
                        )
        await ctx.send(embed=discord.Embed(description="No such guild was found.", colour=self.bot.primary_colour))


def setup(bot):
    bot.add_cog(Admin(bot))

import discord
from discord.ext import commands

import utils.checks as checks


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers with the specified name.",
        usage="findserver <name>",
        hidden=True,
    )
    async def findserver(self, ctx, *, name: str):
        guilds = []
        for guild in self.bot.guilds:
            if guild.name.lower().count(name.lower()) > 0:
                guilds.append(f"{guild.name} `{guild.id}`")
        if len(guilds) == 0:
            await ctx.send(
                embed=discord.Embed(
                    description="No such guild was found.",
                    color=self.bot.error_colour,
                )
            )
        else:
            try:
                await ctx.send(
                    embed=discord.Embed(
                        description="\n".join(guilds),
                        color=self.bot.primary_colour,
                    )
                )
            except discord.HTTPException:
                await ctx.send(
                    embed=discord.Embed(
                        description="The message is too long to be sent.",
                        color=self.bot.error_colour,
                    )
                )

    @checks.is_admin()
    @commands.command(
        description="Get a list of servers the bot shares with the user.",
        usage="sharedservers <user>"
    )
    async def sharedservers(self, ctx, *, user: discord.User):
        guilds = []
        for guild in self.bot.guilds:
            if guild.get_member(user.id) is not None:
                guilds.append(f"{guild.name} `{guild.id}`{' (Owner)' if guild.owner_id == user.id else ''}")
        if len(guilds) == 0:
            await ctx.send(
                embed=discord.Embed(
                    description="No such guild was found.",
                    color=self.bot.error_colour,
                )
            )
        else:
            try:
                await ctx.send(
                    embed=discord.Embed(
                        description="\n".join(guilds),
                        color=self.bot.primary_colour,
                    )
                )
            except discord.HTTPException:
                await ctx.send(
                    embed=discord.Embed(
                        description="The message is too long to be sent.",
                        color=self.bot.error_colour,
                    )
                )

    @checks.is_admin()
    @commands.command(
        description="Create an invite to the specified server.",
        usage="createinvite <server ID>",
        hidden=True,
    )
    async def createinvite(self, ctx, *, guild_id: int):
        for guild in self.bot.guilds:
            if guild.id == guild_id:
                try:
                    invite = (await guild.invites())[0]
                    return await ctx.send(
                        embed=discord.Embed(
                            description=f"Found invite created by {invite.inviter.name}: {invite.url}.",
                            color=self.bot.primary_colour,
                        )
                    )
                except (IndexError, discord.Forbidden):
                    try:
                        return await ctx.send(
                            embed=discord.Embed(
                                description="Created an invite to the server that will expire in 120 seconds: "
                                            f"{(await guild.text_channels[0].create_invite(max_age=120)).url}.",
                                color=self.bot.primary_colour,
                            )
                        )
                    except discord.Forbidden:
                        return await ctx.send(
                            embed=discord.Embed(
                                description="No permissions to create an invite link.",
                                color=self.bot.primary_colour,
                            )
                        )
        await ctx.send(
            embed=discord.Embed(
                description="No such guild was found.",
                color=self.bot.primary_colour,
            )
        )

    @checks.is_admin()
    @commands.command(
        description="Ban a user from the bot",
        usage="banuser <user>",
        hidden=True,
    )
    async def banuser(self, ctx, *, user: discord.User):
        c = self.bot.conn.cursor()
        c.execute("SELECT * FROM banlist WHERE id=? AND type=?", (user.id, "user"))
        res = c.fetchone()
        if not res:
            c.execute("INSERT INTO banlist (id, type) VALUES (?, ?)", (user.id, "user"))
            self.bot.conn.commit()
            self.bot.banned_users.append(user.id)
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully banned that user from the bot.",
                    color=self.bot.primary_colour,
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    description="That user is already banned.",
                    color=self.bot.error_colour,
                )
            )

    @checks.is_admin()
    @commands.command(
        description="Unban a user from the bot",
        usage="unbanuser <user>",
        hidden=True,
    )
    async def unbanuser(self, ctx, *, user: discord.User):
        c = self.bot.conn.cursor()
        c.execute("SELECT * FROM banlist WHERE id=? AND type=?", (user.id, "user"))
        res = c.fetchone()
        if res:
            c.execute("DELETE FROM banlist WHERE id=? AND type=?", (user.id, "user"))
            self.bot.conn.commit()
            self.bot.banned_users.remove(user.id)
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully unbanned that user from the bot.",
                    color=self.bot.primary_colour,
                )
            )
        else:
            await ctx.send(
                embed=discord.Embed(
                    description="That user is not already banned.",
                    color=self.bot.error_colour,
                )
            )


def setup(bot):
    bot.add_cog(Admin(bot))

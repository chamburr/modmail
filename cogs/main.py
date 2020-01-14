import io
import copy
import datetime
import discord
from discord.ext import commands

from utils import checks
from utils import tools
from cogs.modmail_channel import ModMailEvents


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Anonymously reply to the message.", usage="areply <message>")
    async def areply(self, ctx, *, message):
        modmail = ModMailEvents(self.bot)
        await modmail.send_mail_mod(ctx.message, ctx.prefix, True, message)

    async def close_channel(self, ctx, reason, anon: bool = False):
        try:
            await ctx.send(embed=discord.Embed(description="Closing channel...", colour=self.bot.primary_colour))
            data = self.bot.get_data(ctx.guild.id)
            if data[7] == 1:
                messages = await ctx.channel.history(limit=10000).flatten()
            await ctx.channel.delete()
            embed = discord.Embed(
                title="Ticket Closed",
                description=(reason if reason else "No reason was provided."),
                colour=self.bot.error_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_author(
                name=f"{ctx.author.name}#{ctx.author.discriminator}" if anon is False else "Anonymous#0000",
                icon_url=ctx.author.avatar_url if anon is False else "https://cdn.discordapp.com/embed/avatars/0.png",
            )
            embed.set_footer(text=f"{ctx.guild.name} | {ctx.guild.id}", icon_url=ctx.guild.icon_url)
            member = ctx.guild.get_member(tools.get_modmail_user(ctx.channel))
            if member:
                try:
                    data = self.bot.get_data(ctx.guild.id)
                    if data[6]:
                        embed2 = discord.Embed(
                            title="Custom Close Message",
                            description=data[6],
                            colour=self.bot.mod_colour,
                            timestamp=datetime.datetime.utcnow(),
                        )
                        embed2.set_footer(
                            text=f"{ctx.guild.name} | {ctx.guild.id}", icon_url=ctx.guild.icon_url,
                        )
                        await member.send(embed=embed2)
                    await member.send(embed=embed)
                except discord.Forbidden:
                    pass
            if data[4]:
                channel = ctx.guild.get_channel(data[4])
                if channel:
                    try:
                        if member is None:
                            member = await self.bot.fetch_user(tools.get_modmail_user(ctx.channel))
                        if member:
                            embed.set_footer(
                                text=f"{member.name}#{member.discriminator} | {member.id}", icon_url=member.avatar_url,
                            )
                        else:
                            embed.set_footer(
                                text=f"Unknown#0000 | 000000000000000000",
                                icon_url="https://cdn.discordapp.com/embed/avatars/0.png",
                            )
                        if data[7] == 1:
                            history = ""
                            for m in messages:
                                if (
                                    m.author.id != self.bot.user.id
                                    or len(m.embeds) <= 0
                                    or m.embeds[0].title not in ["Message Received", "Message Sent"]
                                ):
                                    continue
                                if not m.embeds[0].author.name:
                                    author = f"{' '.join(m.embeds[0].footer.text.split()[:-2])} (User)"
                                else:
                                    author = f"{m.embeds[0].author.name} (Staff)"
                                description = m.embeds[0].description
                                if len(m.attachments) != 0:
                                    if not description:
                                        description = f"({len(m.attachments)} attachment(s) not shown)"
                                    else:
                                        description = description + f" ({len(m.attachments)} attachment(s) not shown)"
                                history = (
                                    f"[{str(m.created_at.replace(microsecond=0))}] {author}: "
                                    f"{description}\n" + history
                                )
                            history = io.BytesIO(history.encode())
                            file = discord.File(history, f"modmail_log_{tools.get_modmail_user(ctx.channel)}.txt")
                            return await channel.send(embed=embed, file=file)
                        await channel.send(embed=embed)
                    except discord.Forbidden:
                        pass
        except discord.Forbidden:
            await ctx.send(
                embed=discord.Embed(
                    description="Missing permissions to delete this channel.", colour=self.bot.error_colour,
                )
            )

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close the channel.", usage="close [reason]")
    async def close(self, ctx, *, reason: str = None):
        await self.close_channel(ctx, reason)

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Anonymously close the channel.", usage="aclose [reason]")
    async def aclose(self, ctx, *, reason: str = None):
        await self.close_channel(ctx, reason, True)

    @checks.in_database()
    @checks.is_mod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close all of the channel.", usage="closeall [reason]")
    async def closeall(self, ctx, *, reason: str = None):
        category = self.bot.get_data(ctx.guild.id)[2]
        category = ctx.guild.get_channel(category)
        if category:
            for channel in category.text_channels:
                if checks.is_modmail_channel2(self.bot, channel):
                    msg = copy.copy(ctx.message)
                    msg.channel = channel
                    new_ctx = await self.bot.get_context(msg, cls=type(ctx))
                    await self.close_channel(new_ctx, reason)
        try:
            await ctx.send(
                embed=discord.Embed(
                    description="All channels are successfully closed.", colour=self.bot.primary_colour,
                )
            )
        except discord.HTTPException:
            pass

    @checks.in_database()
    @checks.is_mod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Anonymously close all of the channel.", usage="acloseall [reason]")
    async def acloseall(self, ctx, *, reason: str = None):
        category = self.bot.get_data(ctx.guild.id)[2]
        category = ctx.guild.get_channel(category)
        if category:
            for channel in category.text_channels:
                if checks.is_modmail_channel2(self.bot, channel):
                    msg = copy.copy(ctx.message)
                    msg.channel = channel
                    new_ctx = await self.bot.get_context(msg, cls=type(ctx))
                    await self.close_channel(new_ctx, reason, True)
        try:
            await ctx.send(
                embed=discord.Embed(
                    description="All channels are successfully closed anonymously.", colour=self.bot.primary_colour,
                )
            )
        except discord.HTTPException:
            pass

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Blacklist a user from sending messages to this server.",
        usage="blacklist <member>",
        aliases=["block"],
    )
    async def blacklist(self, ctx, *, member: discord.Member):
        blacklist = self.bot.get_data(ctx.guild.id)[9]
        if blacklist is None:
            blacklist = []
        else:
            blacklist = blacklist.split(",")
        if str(member.id) in blacklist:
            return await ctx.send(
                embed=discord.Embed(description="The user is already blacklisted.", colour=self.bot.error_colour)
            )
        blacklist.append(str(member.id))
        blacklist = ",".join(blacklist)
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET blacklist=? WHERE guild=?", (blacklist, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(description="The user is blacklisted successfully.", colour=self.bot.primary_colour)
        )

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Whitelist a user from sending messages to this server.",
        usage="whitelist <member>",
        aliases=["unblock"],
    )
    async def whitelist(self, ctx, *, member: discord.Member):
        blacklist = self.bot.get_data(ctx.guild.id)[9]
        if blacklist is None:
            blacklist = []
        else:
            blacklist = blacklist.split(",")
        if str(member.id) not in blacklist:
            return await ctx.send(
                embed=discord.Embed(description="The user is not blacklisted.", colour=self.bot.error_colour)
            )
        blacklist.remove(str(member.id))
        if len(blacklist) == 0:
            blacklist = None
        else:
            blacklist = ",".join(blacklist)
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET blacklist=? WHERE guild=?", (blacklist, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(description="The user is whitelisted successfully.", colour=self.bot.primary_colour)
        )

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Remove all users from the blacklist.", usage="blacklistclear")
    async def blacklistclear(self, ctx):
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET blacklist=? WHERE guild=?", (None, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(description="The blacklist is cleared successfully.", colour=self.bot.primary_colour)
        )


def setup(bot):
    bot.add_cog(Main(bot))

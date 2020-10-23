import asyncio
import copy
import datetime
import io
import logging

import discord

from discord.ext import commands

from utils import checks
from utils.paginator import Paginator

log = logging.getLogger(__name__)


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Reply to the ticket, useful when anonymous messaging is enabled.",
        usage="reply <message>",
    )
    async def reply(self, ctx, *, message):
        await self.bot.cogs["ModMailEvents"].send_mail_mod(ctx.message, ctx.prefix, False, message)

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Reply to the ticket anonymously.", usage="areply <message>")
    async def areply(self, ctx, *, message):
        await self.bot.cogs["ModMailEvents"].send_mail_mod(ctx.message, ctx.prefix, True, message)

    async def close_channel(self, ctx, reason, anon: bool = False):
        try:
            await ctx.send(embed=discord.Embed(description="Closing channel...", colour=self.bot.primary_colour))
            data = await self.bot.get_data(ctx.guild.id)
            if data[7] is True:
                messages = await ctx.channel.history(limit=10000).flatten()
            await ctx.channel.delete()
            embed = discord.Embed(
                title="Ticket Closed",
                description=(reason if reason else "No reason was provided."),
                colour=self.bot.error_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_author(
                name=str(ctx.author.name) if anon is False else "Anonymous#0000",
                icon_url=ctx.author.avatar_url if anon is False else "https://cdn.discordapp.com/embed/avatars/0.png",
            )
            embed.set_footer(text=f"{ctx.guild.name} | {ctx.guild.id}", icon_url=ctx.guild.icon_url)
            member = ctx.guild.get_member(self.bot.tools.get_modmail_user(ctx.channel))
            if member:
                try:
                    data = await self.bot.get_data(ctx.guild.id)
                    if data[6]:
                        embed2 = discord.Embed(
                            title="Custom Closing Message",
                            description=self.bot.tools.tag_format(data[6], member),
                            colour=self.bot.mod_colour,
                            timestamp=datetime.datetime.utcnow(),
                        )
                        embed2.set_footer(
                            text=f"{ctx.guild.name} | {ctx.guild.id}",
                            icon_url=ctx.guild.icon_url,
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
                            member = await self.bot.fetch_user(self.bot.tools.get_modmail_user(ctx.channel))
                        if member:
                            embed.set_footer(text=f"{member} | {member.id}", icon_url=member.avatar_url)
                        else:
                            embed.set_footer(
                                text="Unknown#0000 | 000000000000000000",
                                icon_url="https://cdn.discordapp.com/embed/avatars/0.png",
                            )
                        if data[7] == 1:
                            history = ""
                            for m in messages:
                                if m.author.bot and (
                                    m.author.id != self.bot.user.id
                                    or len(m.embeds) <= 0
                                    or m.embeds[0].title not in ["Message Received", "Message Sent"]
                                ):
                                    continue
                                if not m.author.bot and m.content == "":
                                    continue
                                author = f"{m.author} (Comment)"
                                description = m.content
                                if m.author.bot:
                                    if not m.embeds[0].author.name:
                                        author = f"{' '.join(m.embeds[0].footer.text.split()[:-2])} (User)"
                                    else:
                                        author = f"{m.embeds[0].author.name} (Staff)"
                                    description = m.embeds[0].description
                                    for attachment in [
                                        field.value
                                        for field in m.embeds[0].fields
                                        if field.name.startswith("Attachment ")
                                    ]:
                                        if not description:
                                            description = f"(Attachment: {attachment})"
                                        else:
                                            description = description + f" (Attachment: {attachment})"
                                history = (
                                    f"[{str(m.created_at.replace(microsecond=0))}] {author}: "
                                    f"{description}\n" + history
                                )
                            history = io.BytesIO(history.encode())
                            file = discord.File(
                                history, f"modmail_log_{self.bot.tools.get_modmail_user(ctx.channel)}.txt"
                            )
                            msg = await channel.send(embed=embed, file=file)
                            log_url = msg.attachments[0].url[39:-4]
                            log_url = log_url.replace("modmail_log_", "")
                            log_url = [hex(int(some_id))[2:] for some_id in log_url.split("/")]
                            log_url = f"https://modmail.xyz/logs/{'-'.join(log_url)}"
                            embed.add_field(name="Message Logs", value=log_url, inline=False)
                            await asyncio.sleep(0.5)
                            await msg.edit(embed=embed)
                            return
                        await channel.send(embed=embed)
                    except discord.Forbidden:
                        pass
        except discord.Forbidden:
            await ctx.send(
                embed=discord.Embed(
                    description="Missing permissions to delete this channel.",
                    colour=self.bot.error_colour,
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
    @commands.command(description="Close the channel anonymously.", usage="aclose [reason]")
    async def aclose(self, ctx, *, reason: str = None):
        await self.close_channel(ctx, reason, True)

    @checks.in_database()
    @checks.is_mod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close all of the channels.", usage="closeall [reason]")
    async def closeall(self, ctx, *, reason: str = None):
        for channel in ctx.guild.text_channels:
            if checks.is_modmail_channel2(self.bot, channel):
                msg = copy.copy(ctx.message)
                msg.channel = channel
                new_ctx = await self.bot.get_context(msg, cls=type(ctx))
                await self.close_channel(new_ctx, reason)
        try:
            await ctx.send(
                embed=discord.Embed(
                    description="All channels are successfully closed.",
                    colour=self.bot.primary_colour,
                )
            )
        except discord.HTTPException:
            pass

    @checks.in_database()
    @checks.is_mod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close all of the channels anonymously.", usage="acloseall [reason]")
    async def acloseall(self, ctx, *, reason: str = None):
        for channel in ctx.guild.text_channels:
            if checks.is_modmail_channel2(self.bot, channel):
                msg = copy.copy(ctx.message)
                msg.channel = channel
                new_ctx = await self.bot.get_context(msg, cls=type(ctx))
                await self.close_channel(new_ctx, reason, True)
        try:
            await ctx.send(
                embed=discord.Embed(
                    description="All channels are successfully closed anonymously.",
                    colour=self.bot.primary_colour,
                )
            )
        except discord.HTTPException:
            pass

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Blacklist a user to prevent them from creating tickets.",
        usage="blacklist <member>",
        aliases=["block"],
    )
    async def blacklist(self, ctx, *, member: discord.Member):
        blacklist = (await self.bot.get_data(ctx.guild.id))[9]
        if member.id in blacklist:
            await ctx.send(
                embed=discord.Embed(description="The user is already blacklisted.", colour=self.bot.error_colour)
            )
            return
        blacklist.append(member.id)
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE data SET blacklist=$1 WHERE guild=$2", blacklist, ctx.guild.id)
        await ctx.send(
            embed=discord.Embed(description="The user is blacklisted successfully.", colour=self.bot.primary_colour)
        )

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Whitelist a user to allow them to creating tickets.",
        usage="whitelist <member>",
        aliases=["unblock"],
    )
    async def whitelist(self, ctx, *, member: discord.Member):
        blacklist = (await self.bot.get_data(ctx.guild.id))[9]
        if member.id not in blacklist:
            await ctx.send(
                embed=discord.Embed(description="The user is not blacklisted.", colour=self.bot.error_colour)
            )
            return
        blacklist.remove(member.id)
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE data SET blacklist=$1 WHERE guild=$2", blacklist, ctx.guild.id)
        await ctx.send(
            embed=discord.Embed(description="The user is whitelisted successfully.", colour=self.bot.primary_colour)
        )

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Remove all users from the blacklist.", usage="blacklistclear")
    async def blacklistclear(self, ctx):
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE data SET blacklist=$1 WHERE guild=$2", [], ctx.guild.id)
        await ctx.send(
            embed=discord.Embed(description="The blacklist is cleared successfully.", colour=self.bot.primary_colour)
        )

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="View the blacklist.", usage="viewblacklist")
    async def viewblacklist(self, ctx):
        blacklist = (await self.bot.get_data(ctx.guild.id))[9]
        if not blacklist:
            await ctx.send(embed=discord.Embed(description="No one is blacklisted.", colour=self.bot.primary_colour))
            return
        all_pages = []
        for chunk in [blacklist[i : i + 25] for i in range(0, len(blacklist), 25)]:
            page = discord.Embed(
                title="Blacklist",
                description="\n".join([f"<@{user}> ({user})" for user in chunk]),
                colour=self.bot.primary_colour,
            )
            page.set_footer(text="Use the reactions to flip pages.")
            all_pages.append(page)
        if len(all_pages) == 1:
            embed = all_pages[0]
            embed.set_footer(text=discord.Embed.Empty)
            await ctx.send(embed=embed)
            return
        paginator = Paginator(length=1, entries=all_pages, use_defaults=True, embed=True, timeout=120)
        await paginator.start(ctx)


def setup(bot):
    bot.add_cog(Core(bot))

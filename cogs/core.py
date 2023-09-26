import asyncio
import copy
import io
import logging

import discord

from discord.ext import commands

from classes.embed import Embed, ErrorEmbed
from utils import checks, tools
from utils.converters import MemberConverter

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
        ctx.message.content = message
        await self.bot.cogs["ModMailEvents"].send_mail_mod(ctx.message, ctx.prefix, anon=False)

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Reply to the ticket anonymously.", usage="areply <message>")
    async def areply(self, ctx, *, message):
        ctx.message.content = message
        await self.bot.cogs["ModMailEvents"].send_mail_mod(ctx.message, ctx.prefix, anon=True)

    async def close_channel(self, ctx, reason, anon: bool = False):
        await ctx.send(Embed("Closing channel..."))

        data = await tools.get_data(self.bot, ctx.guild.id)

        if data[7] is True:
            messages = await ctx.channel.history(limit=10000).flatten()

        try:
            await ctx.channel.delete()
        except discord.Forbidden:
            await ctx.send(ErrorEmbed("Missing permissions to delete this channel."))
            return

        embed = ErrorEmbed(
            "Ticket Closed",
            reason if reason else "No reason was provided.",
            timestamp=True,
        )
        embed.set_author(
            str(ctx.author) if anon is False else "Anonymous#0000",
            ctx.author.avatar_url
            if anon is False
            else "https://cdn.discordapp.com/embed/avatars/0.png",
        )
        embed.set_footer(f"{ctx.guild.name} | {ctx.guild.id}", ctx.guild.icon_url)

        try:
            member = await ctx.guild.fetch_member(tools.get_modmail_user(ctx.channel).id)
        except discord.NotFound:
            member = None
        else:
            dm_channel = tools.get_modmail_channel(self.bot, ctx.channel)

            if data[6]:
                embed2 = Embed(
                    "Closing Message",
                    tools.tag_format(data[6], member),
                    colour=0xFF4500,
                    timestamp=True,
                )
                embed2.set_footer(f"{ctx.guild.name} | {ctx.guild.id}", ctx.guild.icon_url)
                try:
                    await dm_channel.send(embed2)
                except discord.Forbidden:
                    pass

            try:
                await dm_channel.send(embed)
            except discord.Forbidden:
                pass

        if data[4] is None:
            return

        channel = await ctx.guild.get_channel(data[4])
        if channel is None:
            return

        if member is None:
            try:
                member = await self.bot.fetch_user(tools.get_modmail_user(ctx.channel))
            except discord.NotFound:
                pass

        if member:
            embed.set_footer(f"{member} | {member.id}", member.avatar_url)
        else:
            embed.set_footer(
                "Unknown#0000 | 000000000000000000",
                "https://cdn.discordapp.com/embed/avatars/0.png",
            )

        embed.set_author(
            str(ctx.author) if anon is False else f"{ctx.author} (Anonymous)",
            ctx.author.avatar_url,
        )

        if data[7] is True:
            history = ""

            for message in messages:
                if message.author.bot and (
                    message.author.id != self.bot.id
                    or len(message.embeds) <= 0
                    or message.embeds[0].title not in ["Message Received", "Message Sent"]
                ):
                    continue

                if not message.author.bot and message.content == "":
                    continue

                if message.author.bot:
                    if not message.embeds[0].author.name:
                        author = f"{' '.join(message.embeds[0].footer.text.split()[:-2])} (User)"
                    elif message.embeds[0].author.name.endswith(" (Anonymous)"):
                        author = f"{message.embeds[0].author.name[:-12]} (Staff)"
                    else:
                        author = f"{message.embeds[0].author.name} (Staff)"

                    description = message.embeds[0].description

                    for attachment in [
                        field.value
                        for field in message.embeds[0].fields
                        if field.name.startswith("Attachment ")
                    ]:
                        if not description:
                            description = f"(Attachment: {attachment})"
                        else:
                            description += f" (Attachment: {attachment})"
                else:
                    author = f"{message.author} (Comment)"
                    description = message.content

                history = (
                    f"[{str(message.created_at.replace(microsecond=0))}] {author}: {description}\n"
                    + history
                )

            history = io.BytesIO(history.encode())

            file = discord.File(
                history, f"modmail_log_{tools.get_modmail_user(ctx.channel).id}.txt"
            )

            try:
                msg = await channel.send(embed, file=file)
            except discord.Forbidden:
                return

            log_url = msg.attachments[0].url.split("?")[0][39:-4]
            log_url = log_url.replace("modmail_log_", "")
            log_url = [hex(int(some_id))[2:] for some_id in log_url.split("/")]
            log_url = f"{self.bot.config.BASE_URI}/logs/{'-'.join(log_url)}"
            embed.add_field("Message Logs", log_url, False)

            await asyncio.sleep(0.5)
            await msg.edit(embed)
            return

        try:
            await channel.send(embed)
        except discord.Forbidden:
            pass

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @checks.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close the channel.", usage="close [reason]")
    async def close(self, ctx, *, reason: str = None):
        await self.close_channel(ctx, reason)

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @checks.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close the channel anonymously.", usage="aclose [reason]")
    async def aclose(self, ctx, *, reason: str = None):
        await self.close_channel(ctx, reason, True)

    @checks.in_database()
    @checks.is_mod()
    @checks.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close all of the channels.", usage="closeall [reason]")
    async def closeall(self, ctx, *, reason: str = None):
        for channel in await ctx.guild.text_channels():
            if tools.is_modmail_channel(channel):
                msg = copy.copy(ctx.message)
                msg.channel = channel
                new_ctx = await self.bot.get_context(msg, cls=type(ctx))
                await self.close_channel(new_ctx, reason)

        try:
            await ctx.send(Embed("All channels are successfully closed."))
        except discord.HTTPException:
            pass

    @checks.in_database()
    @checks.is_mod()
    @checks.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(
        description="Close all of the channels anonymously.", usage="acloseall [reason]"
    )
    async def acloseall(self, ctx, *, reason: str = None):
        for channel in await ctx.guild.text_channels():
            if tools.is_modmail_channel(channel):
                msg = copy.copy(ctx.message)
                msg.channel = channel
                new_ctx = await self.bot.get_context(msg, cls=type(ctx))
                await self.close_channel(new_ctx, reason, True)

        try:
            await ctx.send(Embed("All channels are successfully closed anonymously."))
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
    async def blacklist(self, ctx, *, member: MemberConverter):
        blacklist = (await tools.get_data(self.bot, ctx.guild.id))[9]
        if member.id in blacklist:
            await ctx.send(ErrorEmbed("The user is already blacklisted."))
            return

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET blacklist=array_append(blacklist, $1) WHERE guild=$2",
                member.id,
                ctx.guild.id,
            )

        await ctx.send(Embed("The user is blacklisted successfully."))

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Whitelist a user to allow them to create tickets.",
        usage="whitelist <member>",
        aliases=["unblock"],
    )
    async def whitelist(self, ctx, *, member: MemberConverter):
        blacklist = (await tools.get_data(self.bot, ctx.guild.id))[9]

        if member.id not in blacklist:
            await ctx.send(ErrorEmbed("The user is not blacklisted."))
            return

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET blacklist=array_remove(blacklist, $1) WHERE guild=$2",
                member.id,
                ctx.guild.id,
            )

        await ctx.send(Embed("The user is whitelisted successfully."))

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Remove all users from the blacklist.", usage="blacklistclear")
    async def blacklistclear(self, ctx):
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE data SET blacklist=$1 WHERE guild=$2", [], ctx.guild.id)

        await ctx.send(Embed("The blacklist is cleared successfully."))

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="View the blacklist.", usage="viewblacklist")
    async def viewblacklist(self, ctx):
        blacklist = (await tools.get_data(self.bot, ctx.guild.id))[9]
        if not blacklist:
            await ctx.send(Embed("No one is blacklisted."))
            return

        all_pages = []
        for chunk in [blacklist[i : i + 25] for i in range(0, len(blacklist), 25)]:
            page = Embed("Blacklist", "\n".join([f"<@{user}> ({user})" for user in chunk]))
            page.set_footer("Use the reactions to flip pages.")
            all_pages.append(page)

        if len(all_pages) == 1:
            embed = all_pages[0]
            embed.set_footer(discord.Embed.Empty)
            await ctx.send(embed)
            return

        await tools.create_paginator(self.bot, ctx, all_pages)


def setup(bot):
    bot.add_cog(Core(bot))

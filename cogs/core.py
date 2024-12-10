import asyncio
import copy
import io
import logging
import time

import discord

from discord.ext import commands

from classes.embed import Embed, ErrorEmbed
from utils import checks, tools
from utils.converters import UserConverter

log = logging.getLogger(__name__)


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Reply to the ticket.", usage="reply <message>", aliases=["r"])
    async def reply(self, ctx, *, message):
        ctx.message.content = message
        await self.bot.cogs["ModMailEvents"].send_mail_mod(ctx.message, ctx.prefix, anon=False)

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Reply to the ticket anonymously.", usage="areply <message>", aliases=["ar"]
    )
    async def areply(self, ctx, *, message):
        ctx.message.content = message
        await self.bot.cogs["ModMailEvents"].send_mail_mod(ctx.message, ctx.prefix, anon=True)

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_premium()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Use AI to generate a response based on the context and the prompt, with "
        "optional additional instructions. This command will prompt for confirmation.",
        usage="aireply <instructions>",
        aliases=["air"],
    )
    async def aireply(self, ctx, *, instructions: str = None):
        if self.bot.ai is None:
            await ctx.send(ErrorEmbed("AI features are disabled."))
            return

        data = await tools.get_data(self.bot, ctx.guild.id)

        history = await self.generate_history(ctx.channel)
        truncated_history = "\n".join(history.splitlines()[-100:])
        prompt = (
            "You are a Discord moderator for a server. The following is the entire history of "
            "the conversation between staff and the user. Please fill in the suitable response "
            "given the transcript. Only give 1 response option. Do not output additional text such "
            "as 'My response would be...'. Try to appear as supportive as possible.\nHere are "
            f"additional information you should consider (if any): {data[13]}\nHere are additional "
            f"instructions for your response (if any): {instructions}\n\nFull transcript: "
            f"{truncated_history}.\n\nStaff response: "
        )

        try:
            response = await self.bot.ai_generate(prompt)
        except Exception:
            await ctx.send(ErrorEmbed("Failed to generate a response."))
            return

        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

        msg = await ctx.send(Embed("AI Reply", response[:2048]))

        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        await self.bot.state.set(
            f"reaction_menu:{msg.channel.id}:{msg.id}",
            {
                "kind": "aireply",
                "end": int(time.time()) + 180,
                "data": {
                    "anon": data[10],
                    "prefix": ctx.prefix,
                    "author": ctx.author.id,
                    "guild": ctx.guild.id,
                },
            },
        )
        await self.bot.state.sadd(
            "reaction_menu_keys",
            f"reaction_menu:{msg.channel.id}:{msg.id}",
        )

    async def generate_history(self, channel):
        history = ""
        messages = await channel.history(limit=10000).flatten()

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

        return history

    async def close_channel(self, ctx, reason, anon: bool = False):
        await ctx.send(Embed("Closing ticket..."))

        data = await tools.get_data(self.bot, ctx.guild.id)

        if data[7] > 0:
            history = await self.generate_history(ctx.channel)

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
        embed.set_footer(f"{ctx.guild.name} | {ctx.guild.id}", ctx.guild.icon_url)

        if anon is False:
            embed.set_author(str(ctx.author), ctx.author.avatar_url)

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
                member = await self.bot.fetch_user(tools.get_modmail_user(ctx.channel).id)
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

        if data[7] > 0:
            file = discord.File(
                io.BytesIO(history.encode()),
                f"modmail_log_{tools.get_modmail_user(ctx.channel).id}.txt",
            )

            try:
                msg = await channel.send(embed, file=file)
            except discord.Forbidden:
                return

            if self.bot.ai is not None and data[7] == 1:
                try:
                    truncated_history = "\n".join(history.splitlines()[-100:])
                    summary = await self.bot.ai_generate(
                        "The following is the entire history of the conversation between staff and "
                        "the user. Please summarise the entire interaction into 1 or 2 sentences. "
                        "Only give 1 response option. Do not output additional text such as 'Here "
                        "is the summary...'.\n\nFull transcript:\n" + truncated_history
                    )
                    embed.add_field("AI Summary", summary[:1024])
                except Exception:
                    pass

            log_url = f"{self.bot.config.BASE_URI}/logs/"
            log_url += f"{hex(channel.id)[2:]}-{hex(msg.id)[2:]}-{hex(msg.attachments[0].id)[2:]}"
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
    @commands.command(description="Close the ticket.", usage="close [reason]", aliases=["c"])
    async def close(self, ctx, *, reason: str = None):
        await self.close_channel(ctx, reason)

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @checks.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(
        description="Close the ticket anonymously.", usage="aclose [reason]", aliases=["ac"]
    )
    async def aclose(self, ctx, *, reason: str = None):
        await self.close_channel(ctx, reason, True)

    @checks.in_database()
    @checks.is_mod()
    @checks.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close all the tickets.", usage="closeall [reason]")
    async def closeall(self, ctx, *, reason: str = None):
        for channel in await ctx.guild.text_channels():
            if tools.is_modmail_channel(channel):
                msg = copy.copy(ctx.message)
                msg.channel = channel
                new_ctx = await self.bot.get_context(msg, cls=type(ctx))
                await self.close_channel(new_ctx, reason)

        try:
            await ctx.send(Embed("All tickets are successfully closed."))
        except discord.HTTPException:
            pass

    @checks.in_database()
    @checks.is_mod()
    @checks.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close all the tickets anonymously.", usage="acloseall [reason]")
    async def acloseall(self, ctx, *, reason: str = None):
        for channel in await ctx.guild.text_channels():
            if tools.is_modmail_channel(channel):
                msg = copy.copy(ctx.message)
                msg.channel = channel
                new_ctx = await self.bot.get_context(msg, cls=type(ctx))
                await self.close_channel(new_ctx, reason, True)

        try:
            await ctx.send(Embed("All tickets are successfully closed anonymously."))
        except discord.HTTPException:
            pass

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Blacklist users to prevent them from creating tickets. If no users are "
        "provided, this will blacklist the user of the current ticket.",
        usage="blacklist [users]",
        aliases=["block"],
    )
    async def blacklist(self, ctx, users: commands.Greedy[UserConverter] = None, *, check=None):
        if users is None:
            users = []
            if tools.is_modmail_channel(ctx.channel):
                try:
                    users.append(await self.bot.fetch_user(tools.get_modmail_user(ctx.channel).id))
                except discord.NotFound:
                    pass

        if len(users) == 0:
            await ctx.send(ErrorEmbed("You must provide users or run this command in a ticket."))
            return

        if check:
            await ctx.send(ErrorEmbed("The user(s) are not found. Please try again."))
            return

        blacklist = (await tools.get_data(self.bot, ctx.guild.id))[9]
        for user in users:
            if user.id not in blacklist:
                blacklist.append(user.id)

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET blacklist=$1 WHERE guild=$2", blacklist, ctx.guild.id
            )

        await ctx.send(Embed("The user(s) are blacklisted successfully."))

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Whitelist users to allow them to create tickets. If no users are provided, "
        "this will whitelist the user of the current ticket.",
        usage="whitelist [users]",
        aliases=["unblock"],
    )
    async def whitelist(self, ctx, users: commands.Greedy[UserConverter] = None, *, check=None):
        if users is None:
            users = []
            if tools.is_modmail_channel(ctx.channel):
                try:
                    users.append(await self.bot.fetch_user(tools.get_modmail_user(ctx.channel).id))
                except discord.NotFound:
                    pass

        if len(users) == 0:
            await ctx.send(ErrorEmbed("You must provide users or run this command in a ticket."))
            return

        if check:
            await ctx.send(ErrorEmbed("The user(s) are not found. Please try again."))
            return

        blacklist = (await tools.get_data(self.bot, ctx.guild.id))[9]
        for user in users:
            if user.id in blacklist:
                blacklist.remove(user.id)

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET blacklist=$1 WHERE guild=$2", blacklist, ctx.guild.id
            )

        await ctx.send(Embed("The user(s) are whitelisted successfully."))

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

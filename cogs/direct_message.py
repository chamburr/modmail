import asyncio
import copy
import datetime
import io
import logging
import string

import discord

from discord.ext import commands

from utils import checks

log = logging.getLogger(__name__)


class DirectMessageEvents(commands.Cog, name="Direct Message"):
    def __init__(self, bot):
        self.bot = bot
        self.guild = None

    async def send_mail(self, message, guild, to_send):
        self.bot.prom.tickets_message.inc({})
        guild = await self.bot.comm.handler("get_guild", -1, {"guild_id": guild})
        if not guild:
            await message.channel.send(
                embed=discord.Embed(description="The server was not found.", colour=self.bot.error_colour)
            )
            return
        member = await self.bot.comm.handler(
            "get_guild_member",
            -1,
            {"guild_id": guild.id, "member_id": message.author.id},
        )
        if not member:
            await message.channel.send(
                embed=discord.Embed(
                    description="You are not in that server, and the message is not sent.",
                    colour=self.bot.error_colour,
                )
            )
            return
        data = await self.bot.get_data(guild.id)
        category = await self.bot.comm.handler(
            "get_guild_channel",
            -1,
            {"guild_id": guild.id, "channel_id": data[2]},
        )
        if not category:
            await message.channel.send(
                embed=discord.Embed(
                    description="A ModMail category is not found. The bot is not set up properly in the server.",
                    colour=self.bot.error_colour,
                )
            )
            return
        if message.author.id in data[9]:
            await message.channel.send(
                embed=discord.Embed(
                    description="That server has blacklisted you from sending a message there.",
                    colour=self.bot.error_colour,
                )
            )
            return
        channels = [
            channel
            for channel in guild.text_channels
            if checks.is_modmail_channel2(self.bot, channel, message.author.id)
        ]
        channel_id = None
        new_ticket = False
        if len(channels) > 0:
            channel_id = channels[0].id
        if not channel_id:
            self.bot.prom.tickets.inc({})
            try:
                name = "".join(
                    x for x in message.author.name.lower() if x not in string.punctuation and x.isprintable()
                )
                if name:
                    name = name + f"-{message.author.discriminator}"
                else:
                    name = message.author.id
                channel_id = (await self.bot.http.create_channel(
                    guild.id,
                    0,
                    name=name,
                    parent_id=category.id,
                    topic=f"ModMail Channel {message.author.id} (Please do not change this)",
                ))["id"]
                new_ticket = True
                log_channel = await self.bot.comm.handler(
                    "get_guild_channel",
                    -1,
                    {"guild_id": guild.id, "channel_id": data[4]},
                )
                if log_channel:
                    try:
                        embed = discord.Embed(
                            title="New Ticket",
                            colour=self.bot.user_colour,
                            timestamp=datetime.datetime.utcnow(),
                        )
                        embed.set_footer(
                            text=f"{message.author.name}#{message.author.discriminator} | {message.author.id}",
                            icon_url=message.author.avatar_url,
                        )
                        await self.bot.http.send_message(log_channel.id, None, embed=embed.to_dict())
                    except discord.Forbidden:
                        pass
            except discord.Forbidden:
                await message.channel.send(
                    embed=discord.Embed(
                        description="The bot is missing permissions to create a channel. Please contact an admin on "
                        "the server.",
                        colour=self.bot.error_colour,
                    )
                )
                return
            except discord.HTTPException as e:
                await message.channel.send(
                    embed=discord.Embed(
                        description="A HTTPException error occurred. Please contact an admin on the server with the "
                        f"following error information: {e.text} ({e.code}).",
                        colour=self.bot.error_colour,
                    )
                )
                return
        try:
            if new_ticket is True:
                prefix = self.bot.tools.get_guild_prefix(self.bot, guild)
                embed = discord.Embed(
                    title="New Ticket",
                    description="Type a message in this channel to reply. Messages starting with the server prefix "
                    f"`{prefix}` are ignored, and can be used for staff discussion. Use the command "
                    f"`{prefix}close [reason]` to close this ticket.",
                    colour=self.bot.primary_colour,
                    timestamp=datetime.datetime.utcnow(),
                )
                embed.set_footer(
                    text=f"{message.author.name}#{message.author.discriminator} | {message.author.id}",
                    icon_url=message.author.avatar_url,
                )
                roles = []
                for role in data[8]:
                    if role == guild.id:
                        roles.append("@everyone")
                    elif role == -1:
                        roles.append("@here")
                    else:
                        roles.append(f"<@&{role}>")
                await self.bot.http.send_message(channel_id, " ".join(roles), embed=embed.to_dict())
                if data[5]:
                    embed = discord.Embed(
                        title="Custom Greeting Message",
                        description=self.bot.tools.tag_format(data[5], message.author),
                        colour=self.bot.mod_colour,
                        timestamp=datetime.datetime.utcnow(),
                    )
                    embed.set_footer(text=f"{guild.name} | {guild.id}", icon_url=guild.icon_url)
                    await message.channel.send(embed=embed)
            embed = discord.Embed(
                title="Message Sent",
                description=to_send,
                colour=self.bot.user_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_footer(text=f"{guild.name} | {guild.id}", icon_url=guild.icon_url)
            files = []
            for file in message.attachments:
                saved_file = io.BytesIO()
                await file.save(saved_file)
                files.append(discord.File(saved_file, file.filename))
            message2 = await message.channel.send(embed=embed, files=files)
            embed.title = "Message Received"
            embed.set_footer(
                text=f"{message.author.name}#{message.author.discriminator} | {message.author.id}",
                icon_url=message.author.avatar_url,
            )
            for count, attachment in enumerate([attachment.url for attachment in message2.attachments], start=1):
                embed.add_field(name=f"Attachment {count}", value=attachment, inline=False)
            for file in files:
                file.reset()
            if files:
                await self.bot.http.send_files(channel_id, embed=embed.to_dict(), files=files)
            else:
                await self.bot.http.send_message(channel_id, None, embed=embed.to_dict())
        except discord.Forbidden:
            try:
                await message2.delete()
            except NameError:
                pass
            await message.channel.send(
                embed=discord.Embed(
                    description="No permission to send message in the channel. Please contact an admin on the server.",
                    colour=self.bot.error_colour,
                )
            )

    async def select_guild(self, message, prefix, msg=None):
        data = await self.bot.comm.handler(
            "get_user_guilds", self.bot.cluster_count, {"user_id": message.author.id}
        )
        guilds = []
        for chunk in data:
            guilds.extend(chunk)
        guild_list = {}
        for guild in guilds:
            channels = [
                channel
                for channel in guild.text_channels
                if checks.is_modmail_channel2(self.bot, channel, message.author.id)
            ]
            channel = None
            if len(channels) > 0:
                channel = channels[0]
            if not channel:
                guild_list[str(guild.id)] = (guild.name, False)
            else:
                guild_list[str(guild.id)] = (guild.name, True)
        embeds = []
        current_embed = None
        for guild, value in guild_list.items():
            if not current_embed:
                current_embed = discord.Embed(
                    title="Select Server",
                    description="Please select the server you want to send this message to. You can do so by reacting "
                    "with the corresponding emote.",
                    colour=self.bot.primary_colour,
                )
                current_embed.set_footer(text="Use the reactions to flip pages.")
            current_embed.add_field(
                name=f"{len(current_embed.fields) + 1}: {value[0]}",
                value=f"{'Create a new ticket.' if value[1] is False else 'Existing ticket.'}\nServer ID: {guild}",
            )
            if len(current_embed.fields) == 10:
                embeds.append(current_embed)
                current_embed = None
        if current_embed:
            embeds.append(current_embed)
        if len(embeds) == 0:
            await message.channel.send(
                embed=discord.Embed(description="Oops... No server found.", colour=self.bot.primary_colour)
            )
            return
        if msg:
            await msg.edit(embed=embeds[0])
        else:
            msg = await message.channel.send(embed=embeds[0])
        reactions = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟", "◀", "▶"]

        async def add_reactions(length):
            await msg.add_reaction("◀")
            await msg.add_reaction("▶")
            for index in range(0, length):
                await msg.add_reaction(reactions[index])

        def reaction_check(reaction2, user2):
            return str(reaction2) in reactions and user2.id == message.author.id and reaction2.message.id == msg.id

        await add_reactions(len(embeds[0].fields))
        page_index = 0
        chosen = -1
        try:
            while chosen < 0:
                reaction, _ = await self.bot.wait_for("reaction_add", check=reaction_check, timeout=60)
                if str(reaction) == "◀":
                    if page_index != 0:
                        page_index = page_index - 1
                        await msg.edit(embed=embeds[page_index])
                        await add_reactions(len(embeds[page_index].fields))
                elif str(reaction) == "▶":
                    if page_index + 1 < len(embeds):
                        page_index = page_index + 1
                        await msg.edit(embed=embeds[page_index])
                        if len(embeds[page_index].fields) != 10:
                            to_remove = reactions[len(embeds[page_index].fields) : -2]
                            msg = await msg.channel.fetch_message(msg.id)
                            for this_reaction in msg.reactions:
                                if str(this_reaction) in to_remove:
                                    await this_reaction.remove(self.bot.user)
                elif reactions.index(str(reaction)) >= 0:
                    chosen = reactions.index(str(reaction))
        except asyncio.TimeoutError:
            await self.remove_reactions(msg)
            await msg.edit(
                embed=discord.Embed(description="Time out. You did not choose anything.", colour=self.bot.error_colour)
            )
            return
        await msg.delete()
        guild = embeds[page_index].fields[chosen].value.split()[-1]
        await self.send_mail(message, int(guild), message.content)

    async def remove_reactions(self, message):
        message = await message.channel.fetch_message(message.id)
        for reaction in message.reactions:
            await reaction.remove(self.bot.user)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return
        prefix = self.bot.config.default_prefix
        if message.content.startswith(prefix):
            return
        if message.author.id in self.bot.banned_users:
            await message.channel.send(
                embed=discord.Embed(description="You are banned from this bot.", colour=self.bot.error_colour)
            )
            return
        if self.bot.config.default_server:
            await self.send_mail(message, self.bot.config.default_server, message.content)
            return
        guild = None
        async for msg in message.channel.history(limit=30):
            if (
                msg.author.id == self.bot.user.id
                and len(msg.embeds) > 0
                and msg.embeds[0].title in ["Message Received", "Message Sent"]
            ):
                guild = msg.embeds[0].footer.text.split()[-1]
                guild = await self.bot.comm.handler("get_guild", -1, {"guild_id": int(guild)})
                break
        msg = None
        confirmation = await self.bot.tools.get_user_settings(self.bot, message.author.id)
        confirmation = True if confirmation is None or confirmation[1] is True else False
        if guild and confirmation is False:
            await self.send_mail(message, guild.id, message.content)
        elif guild and confirmation is True:
            embed = discord.Embed(
                title="Confirmation",
                description=f"You're sending this message to **{guild.name}** (ID: {guild.id}). React with ✅ "
                "to confirm.\nWant to send to another server instead? React with 🔁.\nTo cancel this request, "
                "react with ❌.",
                colour=self.bot.primary_colour,
            )
            embed.set_footer(text=f"Tip: You can disable confirmation messages with the {prefix}confirmation command.")
            msg = await message.channel.send(embed=embed)
            await msg.add_reaction("✅")
            await msg.add_reaction("🔁")
            await msg.add_reaction("❌")

            def reaction_check(reaction2, user2):
                return (
                    str(reaction2) in ["✅", "🔁", "❌"]
                    and user2.id == message.author.id
                    and reaction2.message.id == msg.id
                )

            try:
                reaction, _ = await self.bot.wait_for("reaction_add", check=reaction_check, timeout=60)
            except asyncio.TimeoutError:
                await self.remove_reactions(msg)
                await msg.edit(
                    embed=discord.Embed(
                        description="Time out. You did not choose anything.",
                        colour=self.bot.error_colour,
                    )
                )
                return
            if str(reaction) == "✅":
                await msg.delete()
                await self.send_mail(message, guild.id, message.content)
            elif str(reaction) == "🔁":
                await self.remove_reactions(msg)
                await self.select_guild(message, prefix, msg)
            elif str(reaction) == "❌":
                await self.remove_reactions(msg)
                await msg.edit(
                    embed=discord.Embed(description="Request cancelled successfully.", colour=self.bot.error_colour)
                )
                await asyncio.sleep(5)
                await msg.delete()
        else:
            await self.select_guild(message, prefix)

    @commands.dm_only()
    @commands.command(
        description="Send message to another server, useful when confirmation messages are disabled.",
        usage="new <message>",
        aliases=["create", "switch", "change"],
    )
    async def new(self, ctx, *, message):
        msg = copy.copy(ctx.message)
        msg.content = message
        await self.select_guild(msg, ctx.prefix)

    @commands.dm_only()
    @commands.command(description="Shortcut to send message to a server.", usage="send <server ID> <message>")
    async def send(self, ctx, guild: int, *, message: str):
        await self.send_mail(ctx.message, guild, message)

    @commands.dm_only()
    @commands.command(description="Enable or disable the confirmation message.", usage="confirmation")
    async def confirmation(self, ctx):
        data = await self.bot.tools.get_user_settings(self.bot, ctx.author.id)
        if not data or data[1] is True:
            async with self.bot.pool.acquire() as conn:
                if not data:
                    await conn.execute(
                        "INSERT INTO preference (identifier, confirmation) VALUES ($1, $2)",
                        ctx.author.id,
                        False,
                    )
                else:
                    await conn.execute(
                        "UPDATE preference SET confirmation=$1 WHERE identifier=$2",
                        False,
                        ctx.author.id,
                    )
            await ctx.send(
                embed=discord.Embed(
                    description="Confirmation messages are disabled. To send messages to another server, "
                    f"either use `{ctx.prefix}new <message>` or `{ctx.prefix}send <server ID> <message>`.",
                    colour=self.bot.primary_colour,
                )
            )
            return
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE preference SET confirmation=$1 WHERE identifier=$2",
                True,
                ctx.author.id,
            )
        await ctx.send(
            embed=discord.Embed(description="Confirmation messages are enabled.", colour=self.bot.primary_colour)
        )


def setup(bot):
    bot.add_cog(DirectMessageEvents(bot))

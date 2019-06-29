import io
import copy
import asyncio
import datetime
import discord
from discord.ext import commands

from utils.tools import get_guild_prefix
from utils.tools import get_user_settings


class DirectMessageEvents(commands.Cog, name="Direct Message"):
    def __init__(self, bot):
        self.bot = bot
        self.guild = None

    async def send_mail(self, message, guild, to_send):
        self.bot.total_messages += 1

        def member_in_guild(guild2):
            return guild2.get_member(message.author.id) is not None

        def channel_in_guild(channel2):
            return (
                channel2.name == str(message.author.id)
                and channel2.category_id in self.bot.all_category
            )

        guild = self.bot.get_guild(int(guild))
        if guild is None:
            return await message.channel.send(
                embed=discord.Embed(
                    description="The server was not found.", colour=self.bot.error_colour
                )
            )
        if member_in_guild(guild) is False:
            return await message.channel.send(
                embed=discord.Embed(
                    description="You are not in that server, and the message is not sent.",
                    colour=self.bot.error_colour,
                )
            )
        data = self.bot.get_data(guild.id)
        category = guild.get_channel(data[2])
        if category is None:
            return await message.channel.send(
                embed=discord.Embed(
                    description="A ModMail category is not found. The bot is not set up properly in the server.",
                    colour=self.bot.error_colour,
                )
            )
        if data[9] is not None and str(message.author.id) in data[9].split(","):
            return await message.channel.send(
                embed=discord.Embed(
                    description="That server has blacklisted you from sending a message there.",
                    colour=self.bot.error_colour,
                )
            )
        new_ticket = False
        try:
            channel = next(filter(channel_in_guild, guild.text_channels))
        except StopIteration:
            self.bot.total_tickets += 1
            try:
                channel = await category.create_text_channel(str(message.author.id))
                new_ticket = True
                log_channel = guild.get_channel(data[4])
                if log_channel is not None:
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
                        await log_channel.send(embed=embed)
                    except discord.Forbidden:
                        pass
            except discord.Forbidden:
                return await message.channel.send(
                    embed=discord.Embed(
                        description="The bot is missing permissions to create a channel. Please contact an admin on "
                        "the server.",
                        colour=self.bot.error_colour,
                    )
                )
            except discord.HTTPException:
                return await message.channel.send(
                    embed=discord.Embed(
                        description="A HTTPException error occurred. This is most likely because the server has "
                        "reached the maximum number of channels (500). Please join the support server "
                        "if you cannot figure out what went wrong.",
                        colour=self.bot.error_colour,
                    )
                )
        try:
            if new_ticket is True:
                self.guild = guild
                prefix = get_guild_prefix(self.bot, self)
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
                await channel.send(
                    content=f"<@&{data[8]}>"
                    if data[8] is not None and data[8] not in ["@here", "@everyone"]
                    else data[8],
                    embed=embed,
                )
                if data[5] is not None:
                    embed = discord.Embed(
                        title="Custom Greeting Message",
                        description=data[5],
                        colour=self.bot.mod_colour,
                        timestamp=datetime.datetime.utcnow(),
                    )
                    embed.set_footer(
                        text=f"{guild.name} | {guild.id}", icon_url=guild.icon_url
                    )
                    await message.channel.send(embed=embed)
            embed = discord.Embed(
                title="Message Received",
                description=to_send,
                colour=self.bot.user_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_footer(
                text=f"{message.author.name}#{message.author.discriminator} | {message.author.id}",
                icon_url=message.author.avatar_url,
            )
            files = []
            for file in message.attachments:
                saved_file = io.BytesIO()
                await file.save(saved_file)
                files.append(discord.File(saved_file, file.filename))
            await channel.send(embed=embed, files=files)
            embed.title = "Message Sent"
            embed.set_footer(text=f"{guild.name} | {guild.id}", icon_url=guild.icon_url)
            for file in files:
                file.reset()
            await message.channel.send(embed=embed, files=files)
        except discord.Forbidden:
            return await message.channel.send(
                embed=discord.Embed(
                    description="No permission to send message in the channel. Please contact an admin on the server.",
                    colour=self.bot.error_colour,
                )
            )

    async def select_guild(self, message, prefix, msg=None):
        def member_in_guild(guild2):
            return guild2.get_member(message.author.id) is not None

        def channel_in_guild(channel2):
            return (
                channel2.name == str(message.author.id)
                and channel2.category_id in self.bot.all_category
            )

        guilds = filter(member_in_guild, self.bot.guilds)
        guild_list = {}
        for guild in guilds:
            try:
                channel = next(filter(channel_in_guild, guild.text_channels))
            except StopIteration:
                channel = None
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
                    description="Select the server you want this message to be sent to.\n Tip: You can "
                    f"also use `{prefix}send <server ID> <message>`.",
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
        if current_embed is not None:
            embeds.append(current_embed)
        if msg:
            await msg.edit(embed=embeds[0])
        else:
            msg = await message.channel.send(embed=embeds[0])
        reactions = [
            "1⃣",
            "2⃣",
            "3⃣",
            "4⃣",
            "5⃣",
            "6⃣",
            "7⃣",
            "8⃣",
            "9⃣",
            "🔟",
            "◀",
            "▶",
        ]

        async def add_reactions(length):
            await msg.add_reaction("◀")
            await msg.add_reaction("▶")
            for index in range(0, length):
                await msg.add_reaction(reactions[index])

        def reaction_check(reaction2, user2):
            return (
                str(reaction2) in reactions
                and user2.id == message.author.id
                and reaction2.message.id == msg.id
            )

        await add_reactions(len(embeds[0].fields))
        page_index = 0
        chosen = -1
        try:
            while chosen < 0:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=reaction_check, timeout=60
                )
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
            return await msg.edit(
                embed=discord.Embed(
                    description="Time out. You did not choose anything.",
                    colour=self.bot.error_colour,
                )
            )
        await msg.delete()
        guild = embeds[page_index].fields[chosen].value.split()[-1]
        await self.send_mail(message, guild, message.content)

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
            return await message.channel.send(
                embed=discord.Embed(
                    description="You are banned from this bot.",
                    colour=self.bot.error_colour,
                )
            )
        guild = None
        async for msg in message.channel.history(limit=30):
            if (
                msg.author.id == self.bot.user.id
                and len(msg.embeds) > 0
                and msg.embeds[0].title in ["Message Received", "Message Sent"]
            ):
                guild = msg.embeds[0].footer.text.split()[-1]
                guild = self.bot.get_guild(int(guild))
                break
        msg = None
        confirmation = get_user_settings(self.bot, message.author.id)
        confirmation = (
            True if confirmation is None or confirmation[1] is None else False
        )
        if guild and confirmation is False:
            await self.send_mail(message, guild.id, message.content)
        elif guild and confirmation is True:
            embed = discord.Embed(
                title="Confirmation",
                description=f"You're sending this message to **{guild.name}** (ID: {guild.id}). React with ✅ to "
                "confirm.\nWant to send to another server instead? React with 🔁.\nTo cancel this request, "
                "react with ❌.",
                colour=self.bot.primary_colour,
            )
            embed.set_footer(
                text=f"Tip: You can disable confirmation messages with the {prefix}confirmation command."
            )
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
                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=reaction_check, timeout=60
                )
            except asyncio.TimeoutError:
                await self.remove_reactions(msg)
                return await msg.edit(
                    embed=discord.Embed(
                        description="Time out. You did not choose anything.",
                        colour=self.bot.error_colour,
                    )
                )
            if str(reaction) == "✅":
                await msg.delete()
                await self.send_mail(message, guild.id, message.content)
            elif str(reaction) == "🔁":
                await self.remove_reactions(msg)
                await self.select_guild(message, prefix, msg)
            elif str(reaction) == "❌":
                await self.remove_reactions(msg)
                await msg.edit(
                    embed=discord.Embed(
                        description="Request cancelled successfully.",
                        colour=self.bot.primary_colour,
                    )
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
    @commands.command(
        description="Shortcut to send message to a server.",
        usage="send <server ID> <message>",
    )
    async def send(self, ctx, guild: int, *, message: str):
        await self.send_mail(ctx.message, guild, message)

    @commands.dm_only()
    @commands.command(
        description="Enable or disable the confirmation message.", usage="confirmation"
    )
    async def confirmation(self, ctx):
        data = get_user_settings(self.bot, ctx.author.id)
        c = self.bot.conn.cursor()
        if data is None or data[1] is None:
            if data is None:
                c.execute(
                    "INSERT INTO usersettings (user, confirmation) VALUES (?, ?)",
                    (ctx.author.id, 1),
                )
            elif data[1] is None:
                c.execute(
                    "UPDATE usersettings SET confirmation=? WHERE user=?",
                    (1, ctx.author.id),
                )
            await ctx.send(
                embed=discord.Embed(
                    description="Confirmation messages are disabled. To send messages to another server, "
                    f"either use `{ctx.prefix}new <message>` or `{ctx.prefix}send <server ID> <message>`.",
                    colour=self.bot.primary_colour,
                )
            )
        else:
            c.execute(
                "UPDATE usersettings SET confirmation=? WHERE user=?",
                (None, ctx.author.id),
            )
            await ctx.send(
                embed=discord.Embed(
                    description="Confirmation messages are enabled.",
                    colour=self.bot.primary_colour,
                )
            )
        self.bot.conn.commit()


def setup(bot):
    bot.add_cog(DirectMessageEvents(bot))

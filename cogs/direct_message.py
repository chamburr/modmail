import io
import logging
import string
import time

import discord

from discord.ext import commands

from classes.embed import Embed, ErrorEmbed
from classes.message import Message
from utils import tools
from utils.converters import GuildConverter

log = logging.getLogger(__name__)


class DirectMessageEvents(commands.Cog, name="Direct Message"):
    def __init__(self, bot):
        self.bot = bot
        self.guild = None

    async def send_mail(self, message, guild):
        self.bot.prom.tickets_message.inc({})

        if not guild:
            await message.channel.send(ErrorEmbed("The server was not found."))
            return

        try:
            member = await guild.fetch_member(message.author.id)
        except discord.NotFound:
            await message.channel.send(
                ErrorEmbed("You are not in that server, and the message is not sent.")
            )
            return

        data = await tools.get_data(self.bot, guild.id)

        category = await guild.get_channel(data[2])
        if not category:
            await message.channel.send(
                ErrorEmbed(
                    "A ModMail category is not found. The bot is not set up properly in the server."
                )
            )
            return

        if message.author.id in data[9]:
            await message.channel.send(
                ErrorEmbed("That server has blacklisted you from sending a message there.")
            )
            return

        channel = None
        for text_channel in await guild.text_channels():
            if tools.is_modmail_channel(text_channel, message.author.id):
                channel = text_channel
                break

        if channel is None:
            if data[12] is not None:
                embed = ErrorEmbed(
                    "Ticket Creation Disabled",
                    data[12] if data[12] else "No reason was provided.",
                    timestamp=True,
                )
                embed.set_footer(f"{guild.name} | {guild.id}", guild.icon_url)
                await message.channel.send(embed)
                return

            self.bot.prom.tickets.inc({})

            name = "".join(
                [
                    x
                    for x in message.author.name.lower()
                    if x not in string.punctuation and x.isprintable()
                ]
            )

            if name:
                name = name + f"-{message.author.discriminator}"
            else:
                name = message.author.id

            try:
                channel = await guild.create_text_channel(
                    name=name,
                    category=category,
                    topic=f"ModMail Channel {message.author.id} {message.channel.id} (Please do "
                    "not change this)",
                )
            except discord.HTTPException as e:
                if "Contains words not allowed" in e.text:
                    channel = await guild.create_text_channel(
                        name=message.author.id,
                        category=category,
                        topic=f"ModMail Channel {message.author.id} {message.channel.id} (Please "
                        "do not change this)",
                    )
                elif "Maximum number of channels in category reached" in e.text:
                    await message.channel.send(
                        ErrorEmbed(
                            "The server has reached the maximum number of active tickets. Please "
                            "try again later."
                        )
                    )
                    return
                else:
                    await message.channel.send(
                        ErrorEmbed(
                            "An HTTPException error occurred. Please contact an admin on the "
                            f"server with the following information: {e.text} ({e.code})."
                        )
                    )
                    return

            log_channel = await guild.get_channel(data[4])
            if log_channel:
                embed = Embed(
                    title="New Ticket",
                    colour=0x00FF00,
                    timestamp=True,
                )
                embed.set_footer(
                    f"{message.author.name}#{message.author.discriminator} | "
                    f"{message.author.id}",
                    message.author.avatar_url,
                )

                try:
                    await log_channel.send(embed)
                except discord.Forbidden:
                    pass

            prefix = await tools.get_guild_prefix(self.bot, guild)

            embed = Embed(
                "New Ticket",
                "Type a message in this channel to reply. Messages starting with the server prefix "
                f"`{prefix}` are ignored, and can be used for staff discussion. Use the command "
                f"`{prefix}close [reason]` to close this ticket.",
                timestamp=True,
            )

            if data[11]:
                embed.description = (
                    f"Type `{prefix}reply <message>` in this channel to reply. All other messages "
                    "are ignored, and can be used for staff discussion. Use the command "
                    f"`{prefix}close [reason]` to close this ticket. (Command only mode enabled)"
                )

            embed.add_field("User", f"<@{message.author.id}> ({message.author.id})")
            embed.add_field(
                "Roles",
                "*None*"
                if len(member._roles) == 0
                else " ".join([f"<@&{x}>" for x in member._roles])
                if len(" ".join([f"<@&{x}>" for x in member._roles])) <= 1024
                else f"*{len(member._roles)} roles*",
            )
            embed.set_footer(f"{message.author} | {message.author.id}", message.author.avatar_url)

            roles = []
            for role in data[8]:
                if role == guild.id:
                    roles.append("@everyone")
                elif role == -1:
                    roles.append("@here")
                else:
                    roles.append(f"<@&{role}>")

            try:
                await channel.send(" ".join(roles), embed=embed)
            except discord.HTTPException:
                await message.channel.send(
                    ErrorEmbed(
                        "The bot is missing permissions. Please contact an admin on the server."
                    )
                )
                return

            if data[5]:
                embed = Embed(
                    "Greeting Message",
                    tools.tag_format(data[5], message.author),
                    colour=0xFF4500,
                    timestamp=True,
                )
                embed.set_footer(f"{guild.name} | {guild.id}", guild.icon_url)

                await message.channel.send(embed)

        embed = Embed("Message Sent", message.content, colour=0x00FF00, timestamp=True)
        embed.set_footer(f"{guild.name} | {guild.id}", guild.icon_url)

        files = []
        for file in message.attachments:
            saved_file = io.BytesIO()
            await file.save(saved_file)
            files.append(discord.File(saved_file, file.filename))

        dm_message = await message.channel.send(embed, files=files)

        embed.title = "Message Received"
        embed.set_footer(
            f"{message.author.name}#{message.author.discriminator} | {message.author.id}",
            message.author.avatar_url,
        )

        for count, attachment in enumerate(
            [attachment.url for attachment in dm_message.attachments], start=1
        ):
            embed.add_field(f"Attachment {count}", attachment, False)

        for file in files:
            file.reset()

        try:
            await channel.send(embed, files=files)
        except discord.Forbidden:
            await dm_message.delete()
            await message.channel.send(
                ErrorEmbed("The bot is missing permissions. Please contact an admin on the server.")
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.id:
            return

        if payload.member:
            return

        if payload.emoji.name in ["✅", "🔁", "❌"]:
            menu, channel, msg = await tools.get_reaction_menu(self.bot, payload, "confirmation")
            if menu is None:
                return

            guild = await self.bot.get_guild(menu["data"]["guild"])
            message = Message(state=self.bot.state, channel=channel, data=menu["data"]["msg"])

            if payload.emoji.name == "✅":
                await self.send_mail(message, guild)
                await msg.delete()
            else:
                if payload.emoji.name == "🔁":
                    await msg.edit(Embed("Loading servers..."))
                    self.bot.loop.create_task(tools.select_guild(self.bot, message, msg))
                elif payload.emoji.name == "❌":
                    await msg.edit(ErrorEmbed("Request cancelled successfully."))

                for reaction in ["✅", "🔁", "❌"]:
                    await msg.remove_reaction(reaction, self.bot.user)

            await self.bot.state.delete(f"reaction_menu:{channel.id}:{msg.id}")
            await self.bot.state.srem(
                "reaction_menu_keys",
                f"reaction_menu:{channel.id}:{msg.id}",
            )
            return

        numbers = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"]
        arrows = ["◀️", "▶️"]
        if payload.emoji.name in numbers + arrows:
            menu, channel, msg = await tools.get_reaction_menu(self.bot, payload, "selection")
            if menu is None:
                return

            page = menu["data"]["page"]
            all_pages = menu["data"]["all_pages"]

            if payload.emoji.name not in arrows:
                chosen = numbers.index(payload.emoji.name)
                await msg.delete()

                fields = all_pages[page]["fields"]
                if chosen > len(fields):
                    return

                guild = await self.bot.get_guild(fields[chosen]["value"].split()[-1])
                message = Message(state=self.bot.state, channel=channel, data=menu["data"]["msg"])
                await self.send_mail(message, guild)

                await self.bot.state.delete(f"reaction_menu:{channel.id}:{msg.id}")
                await self.bot.state.srem(
                    "reaction_menu_keys",
                    f"reaction_menu:{channel.id}:{msg.id}",
                )
                return

            if payload.emoji.name == "◀️" and page > 0:
                page -= 1

                new_page = Embed.from_dict(all_pages[page])
                await msg.edit(new_page)

                menu["data"]["page"] = page
                menu["end"] = int(time.time()) + 180
                await self.bot.state.set(f"reaction_menu:{channel.id}:{msg.id}", menu)

                for reaction in numbers[: len(new_page.fields)]:
                    await msg.add_reaction(reaction)

            if payload.emoji.name == "▶️" and page < len(all_pages) - 1:
                page += 1

                new_page = Embed.from_dict(all_pages[page])
                await msg.edit(new_page)

                menu["data"]["page"] = page
                menu["end"] = int(time.time()) + 180
                await self.bot.state.set(f"reaction_menu:{channel.id}:{msg.id}", menu)

                for reaction in numbers[len(new_page.fields) :]:
                    try:
                        await msg.remove_reaction(reaction, self.bot.user)
                    except discord.NotFound:
                        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return

        for prefix in [f"<@{self.bot.id}> ", f"<@!{self.bot.id}> ", self.bot.config.DEFAULT_PREFIX]:
            if message.content.startswith(prefix):
                return

        if await tools.is_user_banned(self.bot, message.author):
            await message.channel.send(ErrorEmbed("You are banned from this bot."))
            return

        guild = None
        confirmation = False
        if self.bot.config.DEFAULT_SERVER is not None:
            guild = await self.bot.get_guild(int(self.bot.config.DEFAULT_SERVER))
        else:
            async for msg in message.channel.history(limit=30):
                if (
                    msg.author.id == self.bot.id
                    and len(msg.embeds) > 0
                    and msg.embeds[0].title in ["Message Received", "Message Sent"]
                ):
                    guild = msg.embeds[0].footer.text.split()[-1]
                    guild = await self.bot.get_guild(int(guild))
                    break

            settings = await tools.get_user_settings(self.bot, message.author.id)
            if settings is None or settings[0] is True:
                confirmation = True

        if guild and confirmation is True:
            embed = Embed(
                "Confirmation",
                f"You're sending this message to **{guild.name}** (ID: {guild.id}). React with ✅ "
                "to confirm.\nWant to send to another server? React with 🔁.\nTo cancel this "
                "request, react with ❌.",
            )
            embed.set_footer(
                "Tip: You can disable confirmation messages with the "
                f"{self.bot.config.DEFAULT_PREFIX}confirmation command."
            )
            msg = await message.channel.send(embed)

            await msg.add_reaction("✅")
            await msg.add_reaction("🔁")
            await msg.add_reaction("❌")

            await self.bot.state.set(
                f"reaction_menu:{msg.channel.id}:{msg.id}",
                {
                    "kind": "confirmation",
                    "end": int(time.time()) + 180,
                    "data": {
                        "guild": guild.id,
                        "msg": message._data,
                    },
                },
            )
            await self.bot.state.sadd(
                "reaction_menu_keys",
                f"reaction_menu:{msg.channel.id}:{msg.id}",
            )
        elif guild:
            await self.send_mail(message, guild)
        else:
            msg = await message.channel.send(Embed("Loading servers..."))
            await tools.select_guild(self.bot, message, msg)

    @commands.dm_only()
    @commands.command(
        description="Send message to another server, useful when confirmation messages are "
        "disabled.",
        usage="new <message>",
        aliases=["create", "switch", "change"],
    )
    async def new(self, ctx, *, message: str):
        ctx.message.content = message
        ctx.message._data["content"] = message

        msg = await ctx.send(Embed("Loading servers..."))
        await tools.select_guild(self.bot, ctx.message, msg)

    @commands.dm_only()
    @commands.command(
        description="Shortcut to send message to a server.", usage="send <server ID> <message>"
    )
    async def send(self, ctx, guild: GuildConverter, *, message: str):
        ctx.message.content = message
        await self.send_mail(ctx.message, guild)

    @commands.dm_only()
    @commands.command(
        description="Enable or disable the confirmation message.", usage="confirmation"
    )
    async def confirmation(self, ctx):
        data = await tools.get_user_settings(self.bot, ctx.author.id)

        if not data or data[0] is True:
            async with self.bot.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO account VALUES ($1, $2, NULL) ON CONFLICT (identifier) DO UPDATE "
                    "SET confirmation=$2",
                    ctx.author.id,
                    False,
                )

            await ctx.send(
                Embed(
                    "Confirmation messages are disabled. To send messages to another server, "
                    f"either use `{ctx.prefix}new <message>` or `{ctx.prefix}send <server ID> "
                    "<message>`.",
                )
            )
            return

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE account SET confirmation=$1 WHERE identifier=$2",
                True,
                ctx.author.id,
            )

        await ctx.send(Embed("Confirmation messages are enabled."))


def setup(bot):
    bot.add_cog(DirectMessageEvents(bot))

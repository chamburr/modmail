import copy
import datetime
import io
import logging
import string
import time

import discord

from discord.ext import commands

import config

from classes.channel import DMChannel
from classes.embed import Embed, ErrorEmbed
from classes.message import Message
from utils import tools

log = logging.getLogger(__name__)


class DirectMessageEvents(commands.Cog, name="Direct Message"):
    def __init__(self, bot):
        self.bot = bot
        self.guild = None

    async def send_mail(self, message, guild, to_send):
        self.bot.prom.tickets_message.inc({})

        if not guild:
            message.channel.send(embed=ErrorEmbed(description="The server was not found."))
            return

        if not await self.bot.state.sismember(f"user:{message.author.id}", guild.id):
            message.channel.send(
                embed=ErrorEmbed(description="You are not in that server, and the message is not sent.")
            )
            return

        data = await self.bot.get_data(guild.id)

        category = await guild.get_channel(data[2])
        if not category:
            await message.channel.send(
                embed=ErrorEmbed(
                    description="A ModMail category is not found. The bot is not set up properly in the server."
                )
            )
            return

        if message.author.id in data[9]:
            await message.channel.send(
                embed=ErrorEmbed(description="That server has blacklisted you from sending a message there.")
            )
            return

        channels = [
            channel for channel in (await guild.text_channels()) if tools.is_modmail_channel(channel, message.author.id)
        ]

        channel = None
        new_ticket = False

        if len(channels) > 0:
            channel = channels[0]
        else:
            new_ticket = True

        if not channel:
            self.bot.prom.tickets.inc({})

            try:
                name = "".join(
                    x for x in message.author.name.lower() if x not in string.punctuation and x.isprintable()
                )

                if name:
                    name = name + f"-{message.author.discriminator}"
                else:
                    name = message.author.id

                channel = await guild.create_text_channel(
                    name=name,
                    category=category,
                    topic=f"ModMail Channel {message.author.id} {message.channel.id} (Please do not change this)",
                )

                log_channel = await guild.get_channel(data[4])
                if log_channel:
                    try:
                        embed = Embed(
                            title="New Ticket",
                            colour=config.user_colour,
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
                await message.channel.send(
                    embed=ErrorEmbed(
                        description="The bot is missing permissions to create a channel. Please contact an admin on "
                        "the server."
                    )
                )
                return
            except discord.HTTPException as e:
                await message.channel.send(
                    embed=ErrorEmbed(
                        description="A HTTPException error occurred. Please contact an admin on the server with the "
                        f"following information: {e.text} ({e.code})."
                    )
                )
                return

        try:
            if new_ticket is True:
                prefix = await tools.get_guild_prefix(self.bot, guild)

                embed = Embed(
                    title="New Ticket",
                    description="Type a message in this channel to reply. Messages starting with the server prefix "
                    f"`{prefix}` are ignored, and can be used for staff discussion. Use the command "
                    f"`{prefix}close [reason]` to close this ticket.",
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

                await channel.send(" ".join(roles), embed=embed)

                if data[5]:
                    embed = Embed(
                        title="Custom Greeting Message",
                        description=tools.tag_format(data[5], message.author),
                        colour=config.mod_colour,
                        timestamp=datetime.datetime.utcnow(),
                    )
                    embed.set_footer(text=f"{guild.name} | {guild.id}", icon_url=guild.icon_url)

                    await message.channel.send(embed=embed)

            embed = Embed(
                title="Message Sent",
                description=to_send,
                colour=config.user_colour,
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

            await channel.send(embed=embed, files=files)
        except discord.Forbidden:
            try:
                await message2.delete()
            except NameError:
                pass
            await message.channel.send(
                embed=ErrorEmbed(
                    description="No permission to send message in the channel. Please contact an admin on the server."
                )
            )

    async def select_guild(self, message, msg=None):
        guilds = [int(guild) for guild in await self.bot.state.smembers(f"user:{message.author.id}")]
        guild_list = {}

        for guild in guilds:
            guild = await self.bot.get_guild(guild)
            channels = [
                channel
                for channel in (await guild.text_channels())
                if tools.is_modmail_channel(channel, message.author.id)
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
                current_embed = Embed(
                    title="Select Server",
                    description="Please select the server you want to send this message to. You can do so by reacting "
                    "with the corresponding emote.",
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
            await message.channel.send(embed=Embed(description="Oops... No server found."))
            return

        if msg:
            await msg.edit(embed=embeds[0])
        else:
            msg = await message.channel.send(embed=embeds[0])

        await message.add_reaction("◀")
        await message.add_reaction("▶")
        for reaction in ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"][: len(embeds[0].fields)]:
            await message.add_reaction(reaction)

        self.bot.state.sadd(
            "selection_menus",
            {
                "channel": msg.channel.id,
                "message": msg.id,
                "msg": message._data,
                "page": 0,
                "all_pages": [embed.to_dict for embed in embeds],
                "end": int(time.time()) + 180,
            },
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.id:
            return

        if payload.member:
            return

        if payload.emoji.name in ["✅", "🔁", "❌"]:
            menus = [
                x
                for x in await self.bot.state.smembers("confirmation_menus")
                if payload.channel_id == x["channel"] and payload.message_id == ["message"]
            ]

            if len(menus) == 0:
                return

            menu = menus[0]
            guild = await self.bot.get_guild(menu["guild"])
            channel = DMChannel(me=self.bot.user, state=self.bot.state, data={"id": menu["channel"]})
            message = Message(state=self.bot.state, channel=channel, data=menu["message"])
            msg = Message(state=self.bot.state, channel=channel, data=menu["msg"])

            if payload.emoji.name == "✅":
                await self.send_mail(msg, guild, msg.content)
                await message.delete()
            else:
                for reaction in ["✅", "🔁", "❌"]:
                    try:
                        await message.remove_reaction(reaction, self.bot.id)
                    except discord.NotFound:
                        pass

                if payload.emoji.name == "🔁":
                    await self.select_guild(msg, message)
                elif payload.emoji.name == "❌":
                    await message.edit(embed=ErrorEmbed(description="Request cancelled successfully."))

            await self.bot.state.srem("confirmation_menus", menu)
            return

        if payload.emoji.name in ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟", "◀️", "▶️"]:
            menus = [
                x
                for x in await self.bot.state.smembers("selection_menus")
                if payload.channel_id == x["channel"] and payload.message_id == ["message"]
            ]

            if len(menus) == 0:
                return

            menu = menus[0]

            page = menu["page"]
            all_pages = menu["all_pages"]

            channel = DMChannel(me=self.bot.user, state=self.bot.state, data={"id": menu["channel"]})
            message = Message(state=self.bot.state, channel=channel, data=menu["message"])

            if payload.emoji.name not in ["◀️", "▶️"]:
                chosen = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"].index(payload.emoji.name)
                await message.delete()

                fields = all_pages[page]["fields"]
                if chosen > len(fields):
                    return

                guild = await self.bot.get_guild(fields[chosen]["value"].split()[-1])
                msg = Message(state=self.bot.state, channel=channel, data=menu["msg"])

                await self.send_mail(msg, guild, msg.content)

                await self.bot.state.srem("selection_menus", menu)
                return

            if payload.emoji.name == "◀️" and page > 0:
                page -= 1
                new_page = discord.Embed.from_dict(all_pages[page])
                await message.edit(embed=new_page)

                for reaction in ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"][: len(new_page.fields)]:
                    await message.add_reaction(reaction)
            elif payload.emoji.name == "▶️" and page < len(all_pages) - 1:
                page += 1
                new_page = discord.Embed.from_dict(all_pages[page])
                await message.edit(embed=new_page)

                for reaction in ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"][len(new_page.fields) :]:
                    try:
                        await message.remove_reaction(reaction, self.bot.id)
                    except discord.NotFound:
                        pass

            await self.bot.state.srem("selection_menus", menu)
            menu["page"] = page
            menu["end"] = int(time.time()) + 180
            await self.bot.state.sadd("selection_menus", menu)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return

        for prefix in [f"<@{self.bot.id}> ", f"<@!{self.bot.id}> ", self.bot.config.default_prefix]:
            if message.content.startswith(prefix):
                return

        if await tools.is_user_banned(self.bot, message.author):
            await message.channel.send(embed=ErrorEmbed(description="You are banned from this bot."))
            return

        if self.bot.config.default_server:
            guild = await self.bot.get_guild(self.bot.config.default_server)
            await self.send_mail(message, guild, message.content)
            return

        guild = None
        async for msg in message.channel.history(limit=30):
            if (
                msg.author.id == self.bot.id
                and len(msg.embeds) > 0
                and msg.embeds[0].title in ["Message Received", "Message Sent"]
            ):
                guild = msg.embeds[0].footer.text.split()[-1]
                guild = await self.bot.get_guild(int(guild))
                break

        confirmation = await tools.get_user_settings(self.bot, message.author.id)
        confirmation = True if confirmation is None or confirmation[0] is True else False

        if guild and confirmation is False:
            await self.send_mail(message, guild, message.content)
        elif guild and confirmation is True:
            embed = Embed(
                title="Confirmation",
                description=f"You're sending this message to **{guild.name}** (ID: {guild.id}). React with ✅ to "
                "confirm.\nWant to send to another server instead? React with 🔁.\nTo cancel this request, react with "
                "❌.",
            )
            embed.set_footer(text=f"Tip: You can disable confirmation messages with the {prefix}confirmation command.")
            msg = await message.channel.send(embed=embed)

            await msg.add_reaction("✅")
            await msg.add_reaction("🔁")
            await msg.add_reaction("❌")

            self.bot.state.sadd(
                "confirmation_menus",
                {
                    "channel": msg.channel.id,
                    "message": msg.id,
                    "guild": guild.id,
                    "msg": message._data,
                    "end": int(time.time()) + 180,
                },
            )
        else:
            await self.select_guild(message)

    @commands.dm_only()
    @commands.command(
        description="Send message to another server, useful when confirmation messages are disabled.",
        usage="new <message>",
        aliases=["create", "switch", "change"],
    )
    async def new(self, ctx, message):
        msg = copy.copy(ctx.message)
        msg.content = message
        await self.select_guild(msg)

    @commands.dm_only()
    @commands.command(description="Shortcut to send message to a server.", usage="send <server ID> <message>")
    async def send(self, ctx, guild: int, *, message: str):
        guild = self.bot.get_guild(guild)
        await self.send_mail(ctx.message, guild, message)

    @commands.dm_only()
    @commands.command(description="Enable or disable the confirmation message.", usage="confirmation")
    async def confirmation(self, ctx):
        data = await tools.get_user_settings(self.bot, ctx.author.id)

        if not data or data[0] is True:
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
                embed=Embed(
                    description="Confirmation messages are disabled. To send messages to another server, "
                    f"either use `{ctx.prefix}new <message>` or `{ctx.prefix}send <server ID> <message>`.",
                )
            )
            return

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE preference SET confirmation=$1 WHERE identifier=$2",
                True,
                ctx.author.id,
            )

        await ctx.send(embed=Embed(description="Confirmation messages are enabled."))


def setup(bot):
    bot.add_cog(DirectMessageEvents(bot))

import copy
import datetime
import io
import logging
import string
import time

import discord

from discord.ext import commands

import config

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
            message.channel.send(embed=ErrorEmbed(description="The server was not found."))
            return

        member = await guild.fetch_member(message.author.id)
        if not member:
            message.channel.send(
                embed=ErrorEmbed(description="You are not in that server, and the message is not sent.")
            )
            return

        data = await tools.get_data(self.bot, guild.id)

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

        channel = None
        for text_channel in await guild.text_channels():
            if tools.is_modmail_channel(text_channel, message.author.id):
                channel = text_channel
                break

        if channel is None:
            self.bot.prom.tickets.inc({})

            name = "".join([x for x in message.author.name.lower() if x not in string.punctuation and x.isprintable()])

            if name:
                name = name + f"-{message.author.discriminator}"
            else:
                name = message.author.id

            try:
                channel = await guild.create_text_channel(
                    name=name,
                    category=category,
                    topic=f"ModMail Channel {message.author.id} {message.channel.id} (Please do not change this)",
                )
            except discord.HTTPException as e:
                await message.channel.send(
                    embed=ErrorEmbed(
                        description="A HTTPException error occurred. Please contact an admin on the server with the "
                        f"following information: {e.text} ({e.code})."
                    )
                )
                return

            log_channel = await guild.get_channel(data[4])
            if log_channel:
                embed = Embed(
                    title="New Ticket",
                    colour=config.user_colour,
                    timestamp=datetime.datetime.utcnow(),
                )
                embed.set_footer(
                    text=f"{message.author.name}#{message.author.discriminator} | {message.author.id}",
                    icon_url=message.author.avatar_url,
                )

                try:
                    await log_channel.send(embed=embed)
                except discord.Forbidden:
                    pass

            prefix = await tools.get_guild_prefix(self.bot, guild)

            embed = Embed(
                title="New Ticket",
                description="Type a message in this channel to reply. Messages starting with the server prefix "
                f"`{prefix}` are ignored, and can be used for staff discussion. Use the command "
                f"`{prefix}close [reason]` to close this ticket.",
                timestamp=datetime.datetime.utcnow(),
            )
            embed.add_field(name="User", value=f"<@{message.author.id}> ({message.author.id})")
            embed.add_field(name="Roles", value=" ".join([f"<@&{x}>" for x in member._roles]))
            embed.set_footer(text=f"{message.author} | {message.author.id}", icon_url=message.author.avatar_url)

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
                    embed=ErrorEmbed(
                        description="The bot is missing permissions. Please contact an admin on the server."
                    )
                )
                return

            if data[5]:
                embed = Embed(
                    title="Greeting Message",
                    description=tools.tag_format(data[5], message.author),
                    colour=config.mod_colour,
                    timestamp=datetime.datetime.utcnow(),
                )
                embed.set_footer(text=f"{guild.name} | {guild.id}", icon_url=guild.icon_url)

                await message.channel.send(embed=embed)

        embed = Embed(
            title="Message Sent",
            description=message.content,
            colour=config.user_colour,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=f"{guild.name} | {guild.id}", icon_url=guild.icon_url)

        files = []
        for file in message.attachments:
            saved_file = io.BytesIO()
            await file.save(saved_file)
            files.append(discord.File(saved_file, file.filename))

        dm_message = await message.channel.send(embed=embed, files=files)

        embed.title = "Message Received"
        embed.set_footer(
            text=f"{message.author.name}#{message.author.discriminator} | {message.author.id}",
            icon_url=message.author.avatar_url,
        )

        for count, attachment in enumerate([attachment.url for attachment in dm_message.attachments], start=1):
            embed.add_field(name=f"Attachment {count}", value=attachment, inline=False)

        for file in files:
            file.reset()

        try:
            await channel.send(embed=embed, files=files)
        except discord.Forbidden:
            await dm_message.delete()
            await message.channel.send(
                embed=ErrorEmbed(description="The bot is missing permissions. Please contact an admin on the server.")
            )

    async def select_guild(self, message, msg=None):
        guilds = {}

        user_guilds = await tools.get_user_guilds(self.bot, message.author.id)
        if len(user_guilds) == 0:
            await message.channel.send(
                embed=ErrorEmbed(
                    description=f"Oops, you don't seem to be in our database. Please login at [this link](https://{self.bot.config.base_uri})."
                )
            )
            return

        for guild in await tools.get_user_guilds(self.bot, message.author.id):

            guild = await self.bot.get_guild(int(guild))

            channel = None
            for text_channel in await guild.text_channels():
                if tools.is_modmail_channel(text_channel, message.author.id):
                    channel = text_channel

            if not channel:
                guilds[str(guild.id)] = (guild.name, False)
            else:
                guilds[str(guild.id)] = (guild.name, True)

        if len(guilds) == 0:
            await message.channel.send(
                embed=ErrorEmbed(
                    description="Oops, no server found. Please change your Discord status to online and try again."
                )
            )
            return

        embeds = []

        for chunk in [list(guilds.items())[i : i + 10] for i in range(0, len(guilds), 10)]:
            embed = Embed(
                title="Select Server",
                description="Please select the server you want to send this message to. You can do so by reacting "
                "with the corresponding emote.",
            )
            embed.set_footer(text="Use the reactions to flip pages.")

            for guild, value in chunk:
                embed.add_field(
                    name=f"{len(embed.fields) + 1}: {value[0]}",
                    value=f"{'Create a new ticket.' if value[1] is False else 'Existing ticket.'}\nServer ID: {guild}",
                )

            embeds.append(embed)

        if msg:
            msg = await msg.edit(embed=embeds[0])
        else:
            msg = await message.channel.send(embed=embeds[0])

        await msg.add_reaction("◀")
        await msg.add_reaction("▶")
        for reaction in ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"][: len(embeds[0].fields)]:
            await msg.add_reaction(reaction)

        await self.bot.state.sadd(
            "reaction_menus",
            {
                "kind": "selection",
                "channel": msg.channel.id,
                "message": msg.id,
                "end": int(time.time()) + 180,
                "data": {
                    "msg": message._data,
                    "page": 0,
                    "all_pages": [embed.to_dict() for embed in embeds],
                },
            },
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.id:
            return

        if payload.member:
            return

        if payload.emoji.name in ["✅", "🔁", "❌"]:
            menu, channel, message = await tools.get_reaction_menu(self.bot, payload, "confirmation")
            if menu is None:
                return

            guild = await self.bot.get_guild(menu["data"]["guild"])
            msg = Message(state=self.bot.state, channel=channel, data=menu["data"]["msg"])

            if payload.emoji.name == "✅":
                await self.send_mail(msg, guild)
                await message.delete()
            else:
                for reaction in ["✅", "🔁", "❌"]:
                    await message.remove_reaction(reaction, self.bot.user)

                if payload.emoji.name == "🔁":
                    await self.select_guild(msg, message)
                elif payload.emoji.name == "❌":
                    await message.edit(embed=ErrorEmbed(description="Request cancelled successfully."))

            await self.bot.state.srem("reaction_menus", menu)
            return

        if payload.emoji.name in ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟", "◀️", "▶️"]:
            menu, channel, message = await tools.get_reaction_menu(self.bot, payload, "selection")
            if menu is None:
                return

            page = menu["data"]["page"]
            all_pages = menu["data"]["all_pages"]

            if payload.emoji.name not in ["◀️", "▶️"]:
                chosen = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"].index(payload.emoji.name)
                await message.delete()

                fields = all_pages[page]["fields"]
                if chosen > len(fields):
                    return

                guild = await self.bot.get_guild(fields[chosen]["value"].split()[-1])
                msg = Message(state=self.bot.state, channel=channel, data=menu["data"]["msg"])
                await self.send_mail(msg, guild)

                await self.bot.state.srem("reaction_menus", menu)
                return

            if payload.emoji.name == "◀️" and page > 0:
                page -= 1

                new_page = discord.Embed.from_dict(all_pages[page])
                await message.edit(embed=new_page)

                for reaction in ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"][: len(new_page.fields)]:
                    await message.add_reaction(reaction)

            if payload.emoji.name == "▶️" and page < len(all_pages) - 1:
                page += 1

                new_page = discord.Embed.from_dict(all_pages[page])
                await message.edit(embed=new_page)

                for reaction in ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"][len(new_page.fields) :]:
                    try:
                        await message.remove_reaction(reaction, self.bot.user)
                    except discord.NotFound:
                        pass

            await self.bot.state.srem("reaction_menus", menu)
            menu["page"] = page
            menu["end"] = int(time.time()) + 180
            await self.bot.state.sadd("reaction_menus", menu)

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
            await self.send_mail(message, guild)
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

        settings = await tools.get_user_settings(self.bot, message.author.id)
        confirmation = True if settings is None or settings[0] is True else False

        if guild and confirmation is True:
            embed = Embed(
                title="Confirmation",
                description=f"You're sending this message to **{guild.name}** (ID: {guild.id}). React with ✅ to "
                "confirm.\nWant to send to another server? React with 🔁.\nTo cancel this request, react with ❌.",
            )
            embed.set_footer(
                text="Tip: You can disable confirmation messages with the "
                f"{self.bot.config.default_prefix}confirmation command."
            )
            msg = await message.channel.send(embed=embed)

            await msg.add_reaction("✅")
            await msg.add_reaction("🔁")
            await msg.add_reaction("❌")

            await self.bot.state.sadd(
                "reaction_menus",
                {
                    "kind": "confirmation",
                    "channel": msg.channel.id,
                    "message": msg.id,
                    "end": int(time.time()) + 180,
                    "data": {
                        "guild": guild.id,
                        "msg": message._data,
                    },
                },
            )
        elif guild:
            await self.send_mail(message, guild)
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
    async def send(self, ctx, guild: GuildConverter, *, message: str):
        ctx.message.content = message
        await self.send_mail(ctx.message, guild)

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
                    description="Confirmation messages are disabled. To send messages to another server, either use "
                    f"`{ctx.prefix}new <message>` or `{ctx.prefix}send <server ID> <message>`.",
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

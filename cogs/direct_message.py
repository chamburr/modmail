import io
import asyncio
import datetime
import discord
from discord.ext import commands

from utils.tools import get_guild_prefix


class DirectMessageEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return
        prefix = self.bot.config.default_prefix
        if message.content.startswith(prefix) and not message.content.startswith(f"{prefix}send"):
            return

        def member_in_guild(guild2):
            return guild2.get_member(message.author.id) is not None

        def channel_in_guild(channel2):
            return channel2.name == str(message.author.id) and channel2.category_id in self.bot.all_category

        if message.content.startswith(f"{prefix}send"):
            guild = message.content.split()[1]
            to_send = " ".join(message.content.split()[2:])
            if not guild or not to_send:
                return await message.channel.send(
                    embed=discord.Embed(
                        description=f"Wrong arguments. The correct usage is `{prefix}send <server ID> <message>`.",
                        color=self.bot.error_colour,
                    )
                )
        else:
            to_send = message.content
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
                        title="Choose Server",
                        description="Select and confirm the server you want this message to be sent to.\n"
                                    f"Tip: You can also use `{prefix}send <server ID> <message>`.",
                        color=self.bot.primary_colour,
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

            msg = await message.channel.send(embed=embeds[0])
            reactions = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟", "◀", "▶"]

            async def add_reactions(length):
                await msg.add_reaction("◀")
                await msg.add_reaction("▶")
                for index in range(0, length):
                    await msg.add_reaction(reactions[index])

            def reaction_check(reaction2, user2):
                if str(reaction2) in reactions and user2.id == message.author.id and reaction2.message.id == msg.id:
                    return True
                else:
                    return False

            await add_reactions(len(embeds[0].fields))
            page_index = 0
            chosen = -1
            try:
                while chosen < 0:
                    reaction, user = await self.bot.wait_for("reaction_add", check=reaction_check, timeout=60)
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
                                to_remove = reactions[len(embeds[page_index].fields):-2]
                                msg = await msg.channel.fetch_message(msg.id)
                                for this_reaction in msg.reactions:
                                    if str(this_reaction) in to_remove:
                                        await this_reaction.remove(self.bot.user)
                    elif reactions.index(str(reaction)) >= 0:
                        chosen = reactions.index(str(reaction))
            except asyncio.TimeoutError:
                return await message.channel.send(
                    embed=discord.Embed(
                        description="Time out. You did not choose anything.",
                        color=self.bot.error_colour,
                    )
                )
            await msg.delete()
            guild = embeds[page_index].fields[chosen].value.split()[-1]
        guild = self.bot.get_guild(int(guild))

        if guild is None:
            return await message.channel.send(
                embed=discord.Embed(
                    description="The guild was not found.",
                    color=self.bot.error_colour,
                )
            )
        if member_in_guild(guild) is False:
            return await message.channel.send(
                embed=discord.Embed(
                    description="You are not in that server.",
                    color=self.bot.error_colour,
                )
            )
        data = self.bot.get_data(guild.id)
        category = guild.get_channel(data[2])
        if category is None:
            return await message.channel.send(
                embed=discord.Embed(
                    description="A ModMail category was not found.",
                    color=self.bot.error_colour,
                )
            )
        new_ticket = False
        try:
            channel = next(filter(lambda x: x.name == str(message.author.id), guild.text_channels))
        except StopIteration:
            try:
                channel = await category.create_text_channel(str(message.author.id))
                new_ticket = True
                log_channel = guild.get_channel(data[4])
                if log_channel is not None:
                    try:
                        embed = discord.Embed(
                            title="New Ticket",
                            color=self.bot.user_colour,
                            timestamp=datetime.datetime.utcnow(),
                        )
                        embed.set_footer(
                            text=f"{message.author.id} | {message.author.name}#{message.author.discriminator}",
                            icon_url=message.author.avatar_url,
                        )
                        await log_channel.send(embed=embed)
                    except discord.Forbidden:
                        pass
            except discord.HTTPException:
                return await message.channel.send(
                    embed=discord.Embed(
                        description="A HTTPException error occurred. This is most likely because the server has "
                                    "reached the maximum number of channels.",
                        color=self.bot.error_colour,
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
                    color=self.bot.primary_colour,
                    timestamp=datetime.datetime.utcnow()
                )
                embed.set_footer(
                    text=f"{message.author.id} | {message.author.name}#{message.author.discriminator}",
                    icon_url=message.author.avatar_url,
                )
                await channel.send(embed=embed)
                if data[5] is not None:
                    embed = discord.Embed(
                        title="Custom Greeting Message",
                        description=data[5],
                        color=self.bot.mod_colour,
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.set_footer(text=guild.name, icon_url=guild.icon_url)
                    await message.channel.send(embed=embed)
            embed = discord.Embed(
                title="Message Received",
                description=to_send,
                color=self.bot.user_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_footer(
                text=f"{message.author.id} | {message.author.name}#{message.author.discriminator}",
                icon_url=message.author.avatar_url,
            )
            files = []
            for file in message.attachments:
                saved_file = io.BytesIO()
                await file.save(saved_file)
                files.append(discord.File(saved_file, file.filename))
            await channel.send(embed=embed, files=files)
            embed.title = "Message Sent"
            embed.set_footer(text=guild.name, icon_url=guild.icon_url)
            for file in files:
                file.reset()
            await message.channel.send(embed=embed, files=files)
        except discord.Forbidden:
            return await message.channel.send(
                embed=discord.Embed(
                    description="No permission to send message in the channel. Please contact an admin on the server.",
                    color=self.bot.error_colour,
                )
            )


def setup(bot):
    bot.add_cog(DirectMessageEvents(bot))

import io
import asyncio
import discord
from discord.ext import commands

from utils.tools import get_guild_prefix


class DirectMessageEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return
        prefix = self.bot.config.default_prefix
        if message.content.startswith(prefix):
            return

        def member_in_guild(guild2):
            if guild2.get_member(message.author.id) is not None:
                return True
            else:
                return False

        def channel_in_guild(channel2):
            if channel2.name == str(message.author.id) and channel2.category_id in self.bot.all_category:
                return True
            else:
                return False

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
                    description="Select and confirm the server you want this message to be sent to.",
                    color=self.bot.primary_colour,
                )
                current_embed.set_footer(text="Use the reactions to flip pages.")
            current_embed.add_field(
                name=value[0],
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
        guild = embeds[page_index].fields[chosen].value.split()[-1]
        guild = self.bot.get_guild(guild)
        if guild is None:
            await message.channel.send(
                embed=discord.Embed(
                    description="The guild was not found.",
                    color=self.bot.error_colour,
                )
            )
        return await message.channel.send(f"You chose {chosen} on page {page_index} which "
                                          f"is {embeds[page_index].fields[chosen].name}")


        member = message.guild.get_member(int(message.channel.name))
        if member is None:
            return await message.channel.send(
                embed=discord.Embed(
                    title="Member Not Found",
                    description="The user might have left the server. "
                                f"Use `{prefix}close [reason]` to close this channel.",
                    color=self.bot.error_colour,
                )
            )
        try:
            embed = discord.Embed(
                title="Message Received",
                description=message.content,
                color=self.bot.mod_colour,
            )
            embed.set_author(
                name=f"{message.author.name}#{message.author.discriminator}",
                icon_url=message.author.avatar_url,
            )
            embed.set_footer(text=message.guild.name, icon_url=message.guild.icon_url)
            files = []
            for file in message.attachments:
                saved_file = io.BytesIO()
                await file.save(saved_file)
                files.append(discord.File(saved_file, file.filename))
            await member.send(embed=embed, files=files)
            embed.title = "Message Sent"
            embed.set_footer(text=f"{member.id} | {member.name}#{member.discriminator}", icon_url=member.avatar_url)
            for file in files:
                file.reset()
            await message.channel.send(embed=embed, files=files)
        except discord.Forbidden:
            return await message.channel.send(
                embed=discord.Embed(
                    title="Failed",
                    description="The message could not be sent. The user might have disabled Direct Messages.",
                    color=self.bot.error_colour,
                )
            )
        try:
            await message.delete()
        except discord.Forbidden:
            pass


def setup(bot):
    bot.add_cog(DirectMessageEvents(bot))

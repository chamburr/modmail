import logging
import time

import discord

from discord.ext import commands

from classes.embed import Embed, ErrorEmbed
from utils import tools

log = logging.getLogger(__name__)


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pipe = self.bot._redis.pipeline()

    @commands.Cog.listener()
    async def on_ready(self, _):
        pass

    async def on_socket_response(self, message):
        if message["t"] == "GUILD_MEMBER_UPDATE":
            if int(message["d"]["user"]["id"]) == self.bot.id:
                member = await self.bot.state.get(
                    f"member:{message['d']['guild_id']}:{self.bot.id}"
                )
                if member:
                    member["roles"] = message["d"]["roles"]
                    await self.bot.state.set(
                        f"member:{message['d']['guild_id']}:{self.bot.id}", member
                    )
        elif message["t"] == "GUILD_CREATE":
            for member in message["d"]["members"]:
                if int(member["user"]["id"]) == self.bot.id:
                    await self.bot.state.set(f"member:{message['d']['id']}:{self.bot.id}", member)
                    return
        elif message["t"] == "GUILD_DELETE":
            if message["d"].get("unavailable"):
                return

            await self.bot.state.delete(f"member:{message['d']['id']}:{self.bot.id}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member and payload.member.bot:
            return

        if payload.emoji.name not in ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]:
            return

        menu, channel, message = await tools.get_reaction_menu(self.bot, payload, "paginator")
        if menu is None:
            return

        if payload.emoji.name == "⏹️":
            try:
                await message.clear_reactions()
            except discord.Forbidden:
                for emoji in ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]:
                    try:
                        await message.remove_reaction(emoji, self.bot.user)
                    except discord.NotFound:
                        pass

            await self.bot.state.srem("reaction_menus", menu)
            return

        page = menu["data"]["page"]
        all_pages = menu["data"]["all_pages"]

        if payload.emoji.name == "⏮️":
            page = 0
        elif payload.emoji.name == "◀️" and page > 0:
            page -= 1
        elif payload.emoji.name == "▶️" and page < len(all_pages) - 1:
            page += 1
        elif payload.emoji.name == "⏭️":
            page = len(all_pages) - 1

        await message.edit(discord.Embed.from_dict(all_pages[page]))

        try:
            member = tools.create_fake_user(payload.user_id)
            await message.remove_reaction(payload.emoji, member)
        except (discord.Forbidden, discord.NotFound):
            pass

        await self.bot.state.srem("reaction_menus", menu)
        menu["data"]["page"] = page
        menu["end"] = int(time.time()) + 180
        await self.bot.state.sadd("reaction_menus", menu)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        if not ctx.command:
            return

        self.bot.prom.commands.inc({"name": ctx.command.name})

        if message.guild:
            if await tools.is_guild_banned(self.bot, message.guild):
                await message.guild.leave()
                return

            permissions = await message.channel.permissions_for(await ctx.guild.me())

            if permissions.send_messages is False:
                return

            if permissions.embed_links is False:
                await message.channel.send(
                    "The Embed Links permission is needed for basic commands to work."
                )
                return

        if await tools.is_user_banned(self.bot, message.author):
            await ctx.send(ErrorEmbed("You are banned from the bot."))
            return

        if (
            ctx.command.cog_name in ["Owner", "Admin"]
            and ctx.author.id in self.bot.config.admins + self.bot.config.owners
        ):
            embed = Embed(ctx.command.name.title(), ctx.message.content, timestamp=True)
            embed.set_author(f"{ctx.author} ({ctx.author.id})", ctx.author.avatar_url)

            if self.bot.config.admin_channel:
                channel = await self.bot.get_channel(self.bot.config.admin_channel)
                if channel:
                    await channel.send(embed)

        if ctx.prefix in [f"<@{self.bot.id}> ", f"<@!{self.bot.id}> "]:
            ctx.prefix = await tools.get_guild_prefix(self.bot, message.guild)

        await self.bot.invoke(ctx)


def setup(bot):
    bot.add_cog(Events(bot))

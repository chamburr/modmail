from __future__ import annotations

import logging
import time

from typing import Any

import discord

from discord.ext import commands
from discord.http import Route

from classes.bot import ModMail
from classes.context import Context
from classes.embed import Embed, ErrorEmbed
from classes.message import Message
from utils import tools

log = logging.getLogger(__name__)


class Events(commands.Cog):
    def __init__(self, bot: ModMail) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.user_id == self.bot.id:
            return

        if payload.member and payload.member.bot:
            return

        if payload.emoji.name in ["✅", "❌"]:
            menu, channel, message = await tools.get_reaction_menu(self.bot, payload, "aireply")
            if menu is None:
                return

            if payload.emoji.name == "✅":
                guild = await self.bot.get_guild(menu["data"]["guild"])
                channel = await guild.get_channel(channel.id)
                message = await channel.fetch_message(message.id)
                message.author = await self.bot.fetch_user(menu["data"]["author"])
                message.content = message.embeds[0].description
                await self.bot.cogs["ModMailEvents"].send_mail_mod(
                    message, menu["data"]["prefix"], anon=menu["data"]["anon"]
                )
            elif payload.emoji.name == "❌":
                try:
                    await message.delete()
                except (discord.Forbidden, discord.NotFound):
                    pass

            await self.bot.state.delete(f"reaction_menu:{channel.id}:{message.id}")
            await self.bot.state.srem(
                "reaction_menu_keys",
                f"reaction_menu:{channel.id}:{message.id}",
            )
            return

        if payload.emoji.name in ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]:
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

                await self.bot.state.delete(f"reaction_menu:{channel.id}:{message.id}")
                await self.bot.state.srem(
                    "reaction_menu_keys",
                    f"reaction_menu:{channel.id}:{message.id}",
                )
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

            await message.edit(Embed.from_dict(all_pages[page]))

            try:
                member = tools.create_fake_user(payload.user_id)
                await message.remove_reaction(payload.emoji, member)
            except (discord.Forbidden, discord.NotFound):
                pass

            menu["data"]["page"] = page
            menu["end"] = int(time.time()) + 180
            await self.bot.state.set(f"reaction_menu:{channel.id}:{message.id}", menu)

    @commands.Cog.listener()
    async def on_interaction_create(self, data: dict[str, Any]) -> None:
        if data.get("type") != 2:
            return

        name = data["data"]["name"]
        options = {x["name"]: str(x["value"]) for x in data["data"].get("options", [])}

        args = ""
        command = self.bot.get_command(name)
        if command:
            for param in command.clean_params.values():
                value = options.get(param.name.lower())
                if value is not None:
                    args += f" {value}"

        try:
            await self.bot.http.request(
                Route(
                    "POST",
                    "/interactions/{interaction_id}/{interaction_token}/callback",
                    interaction_id=data["id"],
                    interaction_token=data["token"],
                ),
                json={"type": 5},
            )
        except discord.HTTPException:
            log.warning(f"Failed to acknowledge the {name} slash command.")
            return

        payload = {
            "id": data["id"],
            "channel_id": data["channel_id"],
            "guild_id": data.get("guild_id"),
            "author": data["member"]["user"] if data.get("member") else data["user"],
            "content": f"<@{self.bot.id}> {name}{args}",
            "edited_timestamp": None,
            "type": 0,
            "pinned": False,
            "mention_everyone": False,
            "tts": False,
            "attachments": [],
            "embeds": [],
            "_interaction": {
                "application_id": data["application_id"],
                "token": data["token"],
                "responded": False,
            },
        }

        if data.get("member"):
            payload["member"] = data["member"]

        await self.bot.state.parse_message_create(payload, None)

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message, cls=Context)

        try:
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

            if ctx.prefix in [f"<@{self.bot.id}> ", f"<@!{self.bot.id}> "]:
                ctx.prefix = await tools.get_guild_prefix(self.bot, message.guild)

            await self.bot.invoke(ctx)
        finally:
            interaction = getattr(message, "_interaction", None)
            if interaction is not None and not interaction.get("responded"):
                interaction["responded"] = True
                try:
                    await self.bot.http.request(
                        Route(
                            "PATCH",
                            "/webhooks/{application_id}/{interaction_token}/messages/@original",
                            application_id=interaction["application_id"],
                            interaction_token=interaction["token"],
                        ),
                        json={"content": "The command was executed."},
                    )
                except discord.HTTPException:
                    pass


async def setup(bot: ModMail) -> None:
    await bot.add_cog(Events(bot))

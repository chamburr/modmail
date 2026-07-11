from __future__ import annotations

import logging

from typing import TYPE_CHECKING, Any

import discord

from discord.ext.commands import context
from discord.http import Route

from classes.message import interaction_body

if TYPE_CHECKING:
    from classes.bot import ModMail

log = logging.getLogger(__name__)


class Context(context.Context["ModMail"]):
    def __init__(self, **kwargs: Any) -> None:
        super(Context, self).__init__(**kwargs)

    async def send(self, *args: Any, **kwargs: Any) -> discord.Message:
        interaction = getattr(self.message, "_interaction", None)

        if interaction is not None and "file" not in kwargs and "files" not in kwargs:
            content = args[0] if args else kwargs.get("content")

            if not interaction.get("responded"):
                interaction["responded"] = True
                route = Route(
                    "PATCH",
                    "/webhooks/{application_id}/{interaction_token}/messages/@original",
                    application_id=interaction["application_id"],
                    interaction_token=interaction["token"],
                )
            else:
                route = Route(
                    "POST",
                    "/webhooks/{application_id}/{interaction_token}",
                    application_id=interaction["application_id"],
                    interaction_token=interaction["token"],
                )

            data = await self.bot.http.request(route, json=interaction_body(content, **kwargs))
            message = self.bot.state.create_message(channel=self.channel, data=data)
            message._interaction = interaction
            return message

        return await self.channel.send(*args, **kwargs)

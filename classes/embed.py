from __future__ import annotations

from typing import Any

import discord

from discord import embeds


class Embed(embeds.Embed):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "colour" not in kwargs:
            kwargs["colour"] = 0x1E90FF

        if kwargs.get("timestamp", False) is True:
            kwargs["timestamp"] = discord.utils.utcnow()

        if len(args) == 2:
            kwargs["title"] = args[0]
            kwargs["description"] = args[1]
        elif len(args) == 1:
            kwargs["description"] = args[0]

        super().__init__(**kwargs)

    def set_author(
        self, name: Any = None, icon_url: Any = None, **kwargs: Any
    ) -> None:
        super().set_author(name=name, icon_url=icon_url, **kwargs)

    def set_footer(
        self, text: Any = None, icon_url: Any = None
    ) -> None:
        super().set_footer(text=text, icon_url=icon_url)

    def set_thumbnail(
        self, url: Any = None
    ) -> None:
        super().set_thumbnail(url=url)

    def add_field(
        self, name: Any = None, value: Any = None, inline: bool = True
    ) -> None:
        super().add_field(name=name, value=value, inline=inline)


class ErrorEmbed(Embed):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "colour" not in kwargs:
            kwargs["colour"] = 0xFF0000

        super().__init__(*args, **kwargs)

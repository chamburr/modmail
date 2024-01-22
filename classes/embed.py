import datetime

import discord

from discord import embeds


class Embed(embeds.Embed):
    def __init__(self, *args, **kwargs):
        if "colour" not in kwargs:
            kwargs["colour"] = 0x1E90FF

        if kwargs.get("timestamp", False) is True:
            kwargs["timestamp"] = datetime.datetime.utcnow()

        if len(args) == 2:
            kwargs["title"] = args[0]
            kwargs["description"] = args[1]
        elif len(args) == 1:
            kwargs["description"] = args[0]

        super().__init__(**kwargs)

    def set_author(self, name=None, icon_url=None, **kwargs):
        super().set_author(name=name, icon_url=icon_url, **kwargs)

    def set_footer(self, text=None, icon_url=None):
        super().set_footer(text=text, icon_url=icon_url)

    def set_thumbnail(self, url=None):
        super().set_thumbnail(url=url)

    def add_field(self, name=None, value=None, inline=True):
        super().add_field(name=name, value=value, inline=inline)


class ErrorEmbed(Embed):
    def __init__(self, *args, **kwargs):
        if "colour" not in kwargs:
            kwargs["colour"] = 0xFF0000

        super().__init__(*args, **kwargs)

from discord import embeds

from config import error_colour, primary_colour


class Embed(embeds.Embed):
    def __init__(self, **kwargs):
        if "colour" not in kwargs:
            kwargs["colour"] = primary_colour

        super().__init__(**kwargs)


class ErrorEmbed(embeds.Embed):
    def __init__(self, **kwargs):
        if "colour" not in kwargs:
            kwargs["colour"] = error_colour

        super().__init__(**kwargs)

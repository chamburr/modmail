import logging

from discord.ext.commands import context

log = logging.getLogger(__name__)


class Context(context.Context):
    def __init__(self, **kwargs):
        super(Context, self).__init__(**kwargs)

    async def send(self, *args, **kwargs):
        return await self.channel.send(*args, **kwargs)

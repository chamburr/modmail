import asyncio
import functools

import prometheus_client as prom

from prometheus_async import aio


class Prometheus:
    def __init__(self, bot):
        self.bot = bot
        self.loop = asyncio.get_event_loop()

        self.latency = prom.Gauge("modmail_latency", "The average latency for shards on this cluster")
        self.events = prom.Counter("modmail_discord_events", "The total number of processed events.", ["type"])
        self.dispatch = prom.Counter("modmail_dispatch_events", "The total number of dispatched events.", ["type"])
        self.http = prom.Counter("modmail_http_requests", "The http requests made.", ["method", "route", "status"])

        self.guilds_join = prom.Counter("modmail_guilds_join", "The number of guilds ModMail is added to.")
        self.guilds_leave = prom.Counter("modmail_guilds_leave", "The number of guilds ModMail is removed from.")

        self.shards = prom.Gauge("modmail_shards", "The total number of shards on this cluster.")
        self.guilds = prom.Gauge("modmail_guilds", "The total number of guilds on this cluster.")
        self.users = prom.Gauge("modmail_users", "The total number of users on this cluster.")

        self.commands = prom.Counter("modmail_commands", "The total number of commands used on the bot.", ["name"])
        self.tickets = prom.Counter("modmail_tickets", "The total number of tickets created by the bot.")
        self.tickets_message = prom.Counter("modmail_tickets_message", "The total number of messages sent in tickets.")

    async def start(self):
        await aio.web.start_http_server(addr="127.0.0.1", port=6000 + self.bot.cluster)
        self.loop.create_task(self.update_stats())
        self.loop.create_task(self.update_latency())

    async def get_counter(self, _name, **kwargs):
        counter = getattr(self, _name)
        if kwargs:
            counter = await self.loop.run_in_executor(
                None, functools.partial(lambda x, y: x.labels(**y), counter, kwargs)
            )
        return counter

    async def inc(self, _name, _value=1, **kwargs):
        counter = await self.get_counter(_name, **kwargs)
        await self.loop.run_in_executor(None, functools.partial(lambda x, y: x.inc(y), counter, _value))

    async def set(self, _name, _value=0, **kwargs):
        counter = await self.get_counter(_name, **kwargs)
        await self.loop.run_in_executor(None, functools.partial(lambda x, y: x.set(y), counter, _value))

    async def update_stats(self):
        while True:
            await self.bot.wait_until_ready()
            await self.set("shards", len(self.bot.shards))
            await self.set("guilds", len(self.bot.guilds))
            await self.set("users", len(self.bot.users))
            await asyncio.sleep(30)

    async def update_latency(self):
        while True:
            if not self.bot.is_ready():
                await self.bot.wait_until_ready()
                await asyncio.sleep(60)
            await self.set("latency", self.bot.latency)
            await asyncio.sleep(10)

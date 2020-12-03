import asyncio
import gc
import os
import platform
import resource

from aioprometheus import Collector, Counter, Gauge, Service


class Prometheus:
    def __init__(self, bot):
        self.bot = bot

        self.msvr = Service()

        if platform.system() == "Linux":
            self.platform = platform
            self.pid = os.path.join("/proc", "self")
            self.pagesize = resource.getpagesize()
            self.ticks = os.sysconf("SC_CLK_TCK")
            self.btime = 0

            with open(os.path.join("/proc", "stat"), "rb") as stat:
                for line in stat:
                    if line.startswith(b"btime "):
                        self.btime = float(line.split()[1])
                        break

        self.vmem = Gauge("process_virtual_memory_bytes", "Virtual memory size in bytes.")
        self.rss = Gauge("process_resident_memory_bytes", "Resident memory size in bytes.")
        self.start_time = Gauge("process_start_time_seconds", "Start time of the process since unix epoch in seconds.")
        self.cpu = Counter("process_cpu_seconds", "Total user and system CPU time spent in seconds.")
        self.fds = Gauge("process_open_fds", "Number of open file descriptors.")

        self.info = Gauge("python_info", "Python platform information.")
        self.collected = Counter("python_gc_objects_collected", "Objects collected during GC.")
        self.uncollectable = Counter("python_gc_objects_uncollectable", "Uncollectable objects found during GC.")
        self.collections = Counter("python_gc_collections", "Number of times this generation was collected.")

        self.latency = Gauge("modmail_latency", "The average latency for shards on this cluster")
        self.events = Counter("modmail_discord_events", "The total number of processed events.")
        self.dispatch = Counter("modmail_dispatch_events", "The total number of dispatched events.")
        self.http = Counter("modmail_http_requests", "The number of http requests sent to Discord.")

        self.guilds_join = Counter("modmail_guilds_join", "The number of guilds ModMail is added to.")
        self.guilds_leave = Counter("modmail_guilds_leave", "The number of guilds ModMail is removed from.")

        self.shards = Gauge("modmail_shards", "The total number of shards on this cluster.")
        self.guilds = Gauge("modmail_guilds", "The total number of guilds on this cluster.")
        self.users = Gauge("modmail_users", "The total number of users on this cluster.")

        self.commands = Counter("modmail_commands", "The total number of commands used on the bot.")
        self.tickets = Counter("modmail_tickets", "The total number of tickets created by the bot.")
        self.tickets_message = Counter("modmail_tickets_message", "The total number of messages sent in tickets.")

    async def start(self):
        for name, value in vars(self).items():
            if issubclass(type(value), Collector):
                self.msvr.register(getattr(self, name))
        await self.msvr.start(addr="127.0.0.1", port=6000 + self.bot.cluster)
        self.msvr._runner._server._kwargs["access_log"] = None
        self.bot.loop.create_task(self.update_bot_stats())

        if platform.system() == "Linux":
            self.bot.loop.create_task(self.update_process_stats())
            self.bot.loop.create_task(self.update_platform_stats())

    async def update_bot_stats(self):
        while True:
            await self.bot.wait_until_ready()
            await asyncio.sleep(60)
            self.shards.set({}, len(self.bot.shards))
            self.guilds.set({}, len(self.bot.guilds))
            self.users.set({}, len(self.bot.users))
            self.latency.set({}, self.bot.latency)
            await asyncio.sleep(10)

    async def update_process_stats(self):
        while True:
            with open(os.path.join(self.pid, "stat"), "rb") as stat:
                parts = stat.read().split(b")")[-1].split()
            self.vmem.set({}, float(parts[20]))
            self.rss.set({}, float(parts[21]) * self.pagesize)
            self.start_time.set({}, float(parts[19]) / self.ticks + self.btime)
            self.cpu.set({}, float(parts[11]) / self.ticks + float(parts[12]) / self.ticks)
            self.fds.set({}, len(os.listdir(os.path.join(self.pid, "fd"))))
            await asyncio.sleep(5)

    async def update_platform_stats(self):
        while True:
            self.info.set(
                {
                    "version": self.platform.python_version(),
                    "implementation": self.platform.python_implementation(),
                    "major": platform.python_version_tuple()[0],
                    "minor": platform.python_version_tuple()[1],
                    "patchlevel": platform.python_version_tuple()[2],
                },
                1,
            )
            for gen, stat in enumerate(gc.get_stats()):
                self.collected.set({"generation": str(gen)}, stat["collected"])
                self.uncollectable.set({"generation": str(gen)}, stat["uncollectable"])
                self.collections.set({"generation": str(gen)}, stat["collections"])
            await asyncio.sleep(5)

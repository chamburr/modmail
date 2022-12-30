import asyncio
import gc
import os
import platform
import resource

from aioprometheus import Counter, Gauge
from aioprometheus.service import Service


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
        self.start_time = Gauge("process_start_time_seconds", "Start time of the process.")
        self.cpu = Counter("process_cpu_seconds", "Total CPU time spent in seconds.")
        self.fds = Gauge("process_open_fds", "Number of open file descriptors.")

        self.info = Gauge("python_info", "Python platform information.")
        self.collected = Counter("python_gc_objects_collected", "Objects collected during GC.")
        self.uncollectable = Counter("python_gc_objects_uncollectable", "Uncollectable GC objects.")
        self.collections = Counter("python_gc_collections", "Number of times collected by GC.")

        self.http = Counter("modmail_http_requests", "Number of http requests sent.")
        self.commands = Counter("modmail_commands", "Number of commands used.")
        self.tickets = Counter("modmail_tickets", "Number of tickets created.")
        self.tickets_message = Counter("modmail_tickets_message", "Number of ticket messages sent.")

    async def start(self):
        await self.msvr.start(addr="127.0.0.1", port=6100 + self.bot.cluster)
        self.msvr._runner._server._kwargs["access_log"] = None

        if platform.system() == "Linux":
            self.bot.loop.create_task(self.update_process_stats())
            self.bot.loop.create_task(self.update_platform_stats())

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

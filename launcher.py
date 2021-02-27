<<<<<<< HEAD
<<<<<<< HEAD
"""
Based on The IdleRPG Discord Bot
Copyright (C) 2018-2021 Diniboy and Gelbpunkt
Copyright (C) 2019-2021 CHamburr

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see https://www.gnu.org/licenses/.
"""

=======
>>>>>>> bruh cham why this so hard
=======
>>>>>>> 54691043a8a98258d1a7ada96ff4177725830f40
import asyncio
import os
import signal
import sys
import time

from datetime import datetime
from pathlib import Path

import aioredis
import discord
import orjson

from aiohttp import web

import config


class Instance:
    def __init__(self, instance_id, loop, main, cluster_count):
        self.id = instance_id
        self.loop = loop
        self.main = main
        self.cluster_count = cluster_count
        self.started_at = None
        self.command = f"{sys.executable} \"{Path.cwd() / 'main.py'}\" {self.id} {cluster_count}"
        self._process = None
        self.status = "initialized"
        self.started_at = 0.0
        self.task = self.loop.create_task(self.start())
        self.task.add_done_callback(self.main.dead_process_handler)

    @property
    def is_active(self):
        return self._process is not None and not self._process.returncode

    async def read_stream(self, stream):
        while self.is_active:
            try:
                line = await stream.readline()
            except (asyncio.LimitOverrunError, ValueError):
                continue
            if line:
                line = line.decode("utf-8")[:-1]
                print(f"[Cluster {self.id}] {line}")
            else:
                break

    async def start(self):
        if self.is_active:
            print(f"[Cluster {self.id}] Already active.")
            return
        self.started_at = time.time()
        self._process = await asyncio.create_subprocess_shell(
            self.command,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=os.setsid,
            limit=1024 * 256,
        )
        self.status = "running"
        self.started_at = time.time()
        print(f"[Cluster {self.id}] The cluster is starting.")
        stdout = self.loop.create_task(self.read_stream(self._process.stdout))
        stderr = self.loop.create_task(self.read_stream(self._process.stderr))
        await asyncio.wait([stdout, stderr])
        return self

    async def stop(self):
        self.status = "stopped"
        os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
        print(f"[Cluster {self.id}] The cluster is killed.")
        await asyncio.sleep(5)

    def kill(self):
        self.status = "stopped"
        os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)

    async def restart(self):
        if self.is_active:
            await self.stop()
        await self.start()


class Scheduler:
    def __init__(self, loop):
        self.loop = loop
        self.redis = None
        self.http = None
        self.reactions = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟", "◀️", "▶️"]

    async def _login(self):
        client = discord.Client()
        await client.http.static_login(config.token, bot=True)
        return client.http

    async def cleanup(self):
        rm = await self.redis.get("reaction_menus")
        if rm:
            rm = orjson.loads(rm)
            filtered_rm = []
            for menu in rm:
                if menu["end"] <= datetime.timestamp(datetime.now()):
                    try:
                        await self.http.clear_reactions(menu["channel"], menu["message"])
                    except discord.Forbidden:
                        for reaction in ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]:
                            await self.http.remove_own_reaction(menu["channel"], menu["message"], reaction)
                else:
                    filtered_rm.append(menu)
            await self.redis.set("reaction_menus", orjson.dumps(filtered_rm).decode("utf-8"))
        sm = await self.redis.get("selection_menus")
        if sm:
            sm = orjson.loads(sm)
            filtered_sm = []
            for menu in sm:
                if menu["end"] <= datetime.timestamp(datetime.now()):
                    channel_id = menu["channel"]
                    message_id = menu["message"]
                    reactions = len(menu["all_pages"][menu["page"]]["fields"])
                    await self.http.remove_own_reaction(channel_id, message_id, "◀")
                    await self.http.remove_own_reaction(channel_id, message_id, "▶")
                    for index in range(reactions):
                        await self.http.remove_own_reaction(channel_id, message_id, self.reactions[index])

                    await self.http.edit_message(
                        menu["channel"],
                        menu["message"],
                        embed=discord.Embed(
                            description="Time out. You did not choose anything.", colour=config.error_colour
                        ).to_dict(),
                    )
                else:
                    filtered_sm.append(menu)
            await self.redis.set("selection_menus", orjson.dumps(filtered_sm).decode("utf-8"))
        cm = await self.redis.get("confirmation_menus")
        if cm:
            cm = orjson.loads(cm)
            filtered_cm = []
            for menu in cm:
                if menu["end"] <= datetime.timestamp(datetime.now()):
                    await self.http.edit_message(
                        menu["channel"],
                        menu["message"],
                        embed=discord.Embed(
                            description="Time out. You did not choose anything.", colour=config.error_colour
                        ).to_dict(),
                    )
                    for reaction in ["✅", "🔁", "❌"]:
                        await self.http.remove_own_reaction(menu["channel"], menu["message"], reaction)
                else:
                    filtered_cm.append(menu)
            await self.redis.set("confirmation_menus", orjson.dumps(filtered_cm).decode("utf-8"))

    async def launch(self):
        self.redis = await aioredis.create_redis_pool(config.redis_url, minsize=5, maxsize=10, loop=self.loop)
        self.http = await self._login()
        while True:
            await self.cleanup()
            await asyncio.sleep(5)


class Main:
    def __init__(self, loop):
        self.loop = loop
        self.instances = []
        self.redis = None

    def dead_process_handler(self, result):
        instance = result.result()
        print(f"[Cluster {instance.id}] The cluster exited with code {instance._process.returncode}.")
        if instance._process.returncode == 0 or instance._process.returncode == -15:
            print(f"[Cluster {instance.id}] The cluster stopped gracefully.")
        else:
            print(f"[Cluster {instance.id}] The cluster is restarting.")
            instance.loop.create_task(instance.start())

    def get_instance(self, iterable, instance_id):
        for element in iterable:
            if getattr(element, "id") == instance_id:
                return element
        return None

    async def handler(self, request):
        if request.path == "/restart":
            for instance in self.instances:
                self.loop.create_task(instance.restart())
        elif request.path == "/stop":
            for instance in self.instances:
                self.loop.create_task(instance.stop())

    # def write_targets(self, clusters):
    #     data = []
    #     for i, shard_list in enumerate(clusters, 1):
    #         if not shard_list:
    #             continue
    #         data.append({"labels": {"cluster": f"{i}"}, "targets": [f"localhost:{6000 + i}"]})
    #     with open("targets.json", "w") as f:
    #         json.dump(data, f, indent=4)

    async def launch(self):
        print(f"[Cluster Manager] Starting a total of {config.clusters} clusters.")
        await asyncio.sleep(10)
        for i in range(config.clusters):
            self.instances.append(Instance(i + 1, self.loop, main=self, cluster_count=config.clusters))

        server = web.Server(self.handler)
        runner = web.ServerRunner(server)
        await runner.setup()
        site = web.TCPSite(runner, config.http_host, config.http_port)
        await site.start()


loop = asyncio.get_event_loop()
main = Main(loop=loop)
loop.create_task(main.launch())
scheduler = Scheduler(loop=loop)
loop.create_task(scheduler.launch())

try:
    loop.run_forever()
except KeyboardInterrupt:

    def shutdown_handler(_loop, context):
        if "exception" not in context or not isinstance(context["exception"], asyncio.CancelledError):
            _loop.default_exception_handler(context)

    loop.set_exception_handler(shutdown_handler)
    for instance in main.instances:
        instance.task.remove_done_callback(main.dead_process_handler)
        instance.kill()
    tasks = asyncio.gather(*asyncio.all_tasks(loop=loop), return_exceptions=True)
    tasks.add_done_callback(lambda t: loop.stop())
    tasks.cancel()
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()

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

import asyncio
import json
import os
import signal
import sys
import time

from pathlib import Path

import aiohttp
import aioredis
import config

payload = {
    "Authorization": f"Bot {config.token}",
    "User-Agent": "DiscordBot (custom, 1.0.0)",
}


async def get_shard_count():
    async with aiohttp.ClientSession() as session, session.get(
        "https://discord.com/api/v8/gateway/bot",
        headers=payload,
    ) as req:
        response = await req.json()
    return response["shards"]


def get_cluster_list(shards):
    base, extra = divmod(shards, config.clusters)
    shards = list(range(shards))
    clusters = []
    for i in range(config.clusters):
        clusters.append(shards[: base + (i < extra)])
        shards = shards[base + (i < extra) :]
    return clusters


class Instance:
    def __init__(self, instance_id, shard_list, shard_count, loop, main, cluster_count):
        self.id = instance_id
        self.shard_list = shard_list
        self.shard_count = shard_count
        self.loop = loop
        self.main = main
        self.cluster_count = cluster_count
        self.started_at = None
        self.command = (
            f"{sys.executable} \"{Path.cwd() / 'main.py'}\" \"{shard_list}\" {shard_count} {self.id} {cluster_count}"
        )
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
        await asyncio.wait([self.read_stream(self._process.stdout), self.read_stream(self._process.stderr)])
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

    async def event_handler(self):
        self.redis = await aioredis.create_pool("redis://localhost", minsize=1, maxsize=2)
        await self.redis.execute_pubsub("SUBSCRIBE", config.ipc_channel)
        channel = self.redis.pubsub_channels[bytes(config.ipc_channel, "utf-8")]
        while await channel.wait_message():
            payload = await channel.get_json(encoding="utf-8")
            if payload.get("scope") != "launcher" or not payload.get("action"):
                pass
            elif payload.get("action") == "restart":
                print(f"[Cluster Manager] Received signal to restart cluster {payload.get('id')}.")
                self.loop.create_task(self.get_instance(self.instances, payload.get("id")).restart())
            elif payload.get("action") == "stop":
                print(f"[Cluster Manager] Received signal to stop cluster {payload.get('id')}.")
                self.loop.create_task(self.get_instance(self.instances, payload.get("id")).stop())
            elif payload.get("action") == "start":
                print(f"[Cluster Manager] Received signal to start cluster {payload.get('id')}.")
                self.loop.create_task(self.get_instance(self.instances, payload.get("id")).start())
            elif payload.get("action") == "roll_restart":
                print("[Cluster Manager] Received signal to perform a rolling restart.")
                for instance in self.instances:
                    self.loop.create_task(instance.restart())
                    await asyncio.sleep(len(self.instances[0].shard_list) * 8)

    async def close(self):
        await self.redis.execute_pubsub("UNSUBSCRIBE", config.ipc_channel)
        self.redis.close()

    def write_targets(self, clusters):
        data = []
        for i, shard_list in enumerate(clusters, 1):
            if not shard_list:
                continue
            data.append({"labels": {"cluster": f"{i}"}, "targets": [f"localhost:{6000 + i}"]})
        with open("targets.json", "w") as f:
            json.dump(data, f, indent=4)

    async def launch(self):
        self.loop.create_task(self.event_handler())
        shard_count = await get_shard_count() + config.additional_shards
        clusters = get_cluster_list(shard_count)
        if config.testing is False:
            self.write_targets(clusters)
        print(f"[Cluster Manager] Starting a total of {len(clusters)} clusters.")
        for i, shard_list in enumerate(clusters, 1):
            if not shard_list:
                continue
            self.instances.append(
                Instance(i, shard_list, shard_count, self.loop, main=self, cluster_count=len(clusters))
            )
            await asyncio.sleep(len(clusters[0]) * 8)


loop = asyncio.get_event_loop()
main = Main(loop=loop)
loop.create_task(main.launch())

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
    loop.run_until_complete(main.close())
    tasks = asyncio.gather(*asyncio.all_tasks(loop=loop), return_exceptions=True)
    tasks.add_done_callback(lambda t: loop.stop())
    tasks.cancel()
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()

import asyncio
import json
import os
import signal
import sys
import time

from pathlib import Path

import aiohttp
import aioredis
import asyncpg
import discord
import orjson

from aiohttp import web

import config

from utils.tools import parse_redis_config


async def migrations(filename, connection):
    with open(filename, "r") as f:
        sql = " ".join(f.readlines())
    async with connection.acquire() as conn:
        await conn.execute(sql)


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
        self.bot_id = None
        self.bot_shard_count = None

        self.session = None

    async def bot_stats_updater(self):
        while True:
            if not self.bot_id and not self.bot_shard_count:
                continue
            guilds = await self.redis.scard("guild_keys")
            await self.session.post(
                f"https://top.gg/api/bots/{self.bot_id}/stats",
                data=orjson.dumps({"server_count": guilds, "shard_count": await self.bot_shard_count}),
                headers={"Authorization": config.topgg_token, "Content-Type": "application/json"},
            )
            await self.session.post(
                f"https://discord.bots.gg/api/v1/bots/{self.bot_id}/stats",
                data=orjson.dumps({"guildCount": guilds, "shardCount": await self.bot_shard_count}),
                headers={"Authorization": config.dbots_token, "Content-Type": "application/json"},
            )
            await self.session.post(
                f"https://discordbotlist.com/api/v1/bots/{self.bot_id}/stats",
                data=orjson.dumps({"guilds": guilds}),
                headers={"Authorization": config.dbl_token, "Content-Type": "application/json"},
            )
            await self.session.post(
                f"https://bots.ondiscord.xyz/bot-api/bots/{self.bot_id}/guilds",
                data=orjson.dumps({"guildCount": guilds}),
                headers={"Authorization": config.bod_token, "Content-Type": "application/json"},
            )
            await self.session.post(
                f"https://botsfordiscord.com/api/bot/{self.bot_id}",
                data=orjson.dumps({"server_count": guilds}),
                headers={"Authorization": config.bfd_token, "Content-Type": "application/json"},
            )
            await self.session.post(
                f"https://discord.boats/api/v2/bot/{self.bot_id}",
                data=orjson.dumps({"server_count": guilds}),
                headers={"Authorization": config.dboats_token, "Content-Type": "application/json"},
            )
            await asyncio.sleep(900)

    async def cleanup(self):
        rm = await self.redis.smembers("reaction_menus")
        for menu in rm:
            menu = orjson.loads(menu)
            if menu["end"] <= int(time.time()):
                try:
                    await self.http.clear_reactions(menu["channel"], menu["message"])
                except discord.Forbidden:
                    for reaction in ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]:
                        await self.http.remove_own_reaction(menu["channel"], menu["message"], reaction)
                await self.redis.srem("reaction_menus", orjson.dumps(menu).decode("utf-8"))
        sm = await self.redis.smembers("selection_menus")
        for menu in sm:
            menu = orjson.loads(menu)
            if menu["end"] <= int(time.time()):
                channel_id = menu["channel"]
                message_id = menu["message"]
                reactions = len(menu["all_pages"][menu["page"]]["fields"])
                await self.http.remove_own_reaction(channel_id, message_id, "◀")
                await self.http.remove_own_reaction(channel_id, message_id, "▶")
                for index in range(reactions):
                    await self.http.remove_own_reaction(
                        channel_id,
                        message_id,
                        ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟", "◀️", "▶️"][index],
                    )

                await self.http.edit_message(
                    menu["channel"],
                    menu["message"],
                    embed=discord.Embed(
                        description="Time out. You did not choose anything.", colour=config.error_colour
                    ).to_dict(),
                )
                await self.redis.srem("selection_menus", orjson.dumps(menu).decode("utf-8"))
        cm = await self.redis.smembers("confirmation_menus")
        for menu in cm:
            menu = orjson.loads(menu)
            if menu["end"] <= int(time.time()):
                await self.http.edit_message(
                    menu["channel"],
                    menu["message"],
                    embed=discord.Embed(
                        description="Time out. You did not choose anything.", colour=config.error_colour
                    ).to_dict(),
                )
                for reaction in ["✅", "🔁", "❌"]:
                    await self.http.remove_own_reaction(menu["channel"], menu["message"], reaction)
                await self.redis.srem("confirmation_menus", orjson.dumps(menu).decode("utf-8"))

    async def launch(self):
        client = discord.Client()
        await client.http.static_login(config.token, bot=True)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.http = client.http
        self.redis = await aioredis.create_redis_pool(
            parse_redis_config(config.redis), minsize=5, maxsize=10, loop=self.loop
        )
        self.bot_id = (orjson.loads(await self.redis.get("bot_user")))["id"]
        self.bot_shard_count = int(await self.redis.get("gateway_shards"))
        if config.testing is False:
            await self.bot_stats_updater()
        while True:
            await self.cleanup()
            await asyncio.sleep(5)


class Main:
    def __init__(self, loop):
        self.loop = loop
        self.instances = []
        self.session = None
        self._pool = None

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
        elif request.path == "/healthcheck":
            return web.Response(body={"status": "OK"}, content_type="application/json")
        elif request.path == "/status":
            data = [{"cluster": x.id, "status": "OK" if x.status == "running" else "ERROR"} for x in self.instances]
            return web.Response(body=data, content_type="application/json")

    def write_targets(self, clusters):
        data = []
        for i in range(len(clusters)):
            data.append({"labels": {"cluster": f"{i}"}, "targets": [f"localhost:{6000 + i}"]})
        with open("targets.json", "w") as f:
            json.dump(data, f, indent=4)

    async def launch(self):
        print(f"[Cluster Manager] Starting a total of {config.clusters} clusters.")
        self.session = aiohttp.ClientSession(loop=self.loop)
        self._pool = await asyncpg.create_pool(**config.database, max_size=10, command_timeout=60)
        await migrations("schema.sql", self._pool)
        while True:
            try:
                resp = await self.session.get(f"http://{config.td_host}:{config.td_port}/healthcheck")
                async with resp:
                    if await resp.json() == {"status": "OK"}:
                        break
            except Exception:
                pass
            await asyncio.sleep(5)
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

import asyncio
import json
import os
import signal
import sys
import time

from datetime import datetime
from pathlib import Path

import aiohttp
import discord
import orjson

from aiohttp import web

from classes.bot import ModMail
from classes.embed import ErrorEmbed
from classes.message import Message
from utils import tools
from utils.config import Config

VERSION = "3.3.0"


class Instance:
    def __init__(self, instance_id, loop, main):
        self.id = instance_id
        self.loop = loop
        self.main = main
        self._process = None
        self.status = "initialized"
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

        self._process = await asyncio.create_subprocess_shell(
            f"{sys.executable} \"{Path.cwd() / 'worker.py'}\" {self.id} {config.BOT_CLUSTERS} "
            f"{self.main.bot.id} {VERSION}",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=os.setsid,
            limit=1024 * 256,
        )

        self.status = "running"

        print(f"[Cluster {self.id}] The cluster is starting.")

        stdout = self.loop.create_task(self.read_stream(self._process.stdout))
        stderr = self.loop.create_task(self.read_stream(self._process.stderr))

        await asyncio.wait([stdout, stderr])

        return self

    def kill(self):
        self.status = "stopped"
        os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)

    async def restart(self):
        if self.is_active:
            self.kill()
            await asyncio.sleep(1)

        await self.start()


class Scheduler:
    def __init__(self, loop, bot):
        self.loop = loop
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def premium_updater(self):
        while True:
            async with self.bot.pool.acquire() as conn:
                premium = await conn.fetch(
                    "SELECT identifier, guild FROM premium WHERE expiry IS NOT NULL AND expiry<$1",
                    int(datetime.utcnow().timestamp() * 1000),
                )

                for row in premium:
                    for guild in row[1]:
                        await conn.execute(
                            "UPDATE data SET welcome=$1, goodbye=$2, loggingplus=$3 WHERE guild=$4",
                            None,
                            None,
                            False,
                            guild,
                        )
                        await conn.execute("DELETE FROM snippet WHERE guild=$1", guild)

                    await conn.execute("DELETE FROM premium WHERE identifier=$1", row[0])

            await asyncio.sleep(60)

    async def bot_stats_updater(self):
        while True:
            guilds = await self.bot.state.scard("guild_keys")
            shards = await self.bot.shard_count()

            await self.session.post(
                f"https://top.gg/api/bots/{self.bot.id}/stats",
                data=orjson.dumps({"server_count": guilds, "shard_count": shards}),
                headers={"Authorization": config.TOPGG_TOKEN, "Content-Type": "application/json"},
            )

            await self.session.post(
                f"https://discord.bots.gg/api/v1/bots/{self.bot.id}/stats",
                data=orjson.dumps({"guildCount": guilds, "shardCount": shards}),
                headers={"Authorization": config.DBOTS_TOKEN, "Content-Type": "application/json"},
            )

            await self.session.post(
                f"https://discordbotlist.com/api/v1/bots/{self.bot.id}/stats",
                data=orjson.dumps({"guilds": guilds}),
                headers={"Authorization": config.DBL_TOKEN, "Content-Type": "application/json"},
            )

            await self.session.post(
                f"https://bots.ondiscord.xyz/bot-api/bots/{self.bot.id}/guilds",
                data=orjson.dumps({"guildCount": guilds}),
                headers={"Authorization": config.BOD_TOKEN, "Content-Type": "application/json"},
            )

            await asyncio.sleep(900)

    async def cleanup(self):
        while True:
            for menu_key in await self.bot.state.smembers("reaction_menu_keys"):
                menu = await self.bot.state.get(menu_key)

                if menu is None:
                    await self.bot.state.srem("reaction_menu_keys", menu_key)
                    continue

                if menu["end"] > int(time.time()):
                    continue

                channel = tools.create_fake_channel(self.bot, menu_key.split(":")[1])
                message = tools.create_fake_message(self.bot, channel, menu_key.split(":")[2])

                emojis = []

                if menu["kind"] == "paginator":
                    try:
                        await message.clear_reactions()
                    except discord.Forbidden:
                        emojis = ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]
                    except discord.HTTPException:
                        pass
                elif menu["kind"] == "confirmation":
                    emojis = ["✅", "🔁", "❌"]
                    try:
                        await message.edit(ErrorEmbed("Time out. You did not choose anything."))
                    except discord.HTTPException:
                        emojis = []
                elif menu["kind"] == "selection":
                    emojis = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟", "◀️", "▶️"]
                    try:
                        await message.edit(ErrorEmbed("Time out. You did not choose anything."))
                    except discord.HTTPException:
                        emojis = []

                await self.bot.state.delete(menu_key)
                await self.bot.state.srem("reaction_menu_keys", menu_key)

                for emoji in emojis:
                    try:
                        await message.remove_reaction(emoji, self.bot.user)
                    except discord.HTTPException:
                        pass

            await asyncio.sleep(30)

    async def launch(self):
        async with self.bot.pool.acquire() as conn:
            data = await conn.fetch("SELECT guild, prefix FROM data")
            bans = await conn.fetch("SELECT identifier, category FROM ban")

        if len(data) >= 1:
            await self.bot.state.set(
                [y for x in data for y in (f"prefix:{x[0]}", "" if x[1] is None else x[1])]
            )

        if len([x[0] for x in bans if x[1] == 0]) >= 1:
            await self.bot.state.sadd("banned_users", *[x[0] for x in bans if x[1] == 0])

        if len([x[0] for x in bans if x[1] == 1]) >= 1:
            await self.bot.state.sadd("banned_guilds", *[x[0] for x in bans if x[1] == 1])

        if config.ENVIRONMENT == "production":
            self.loop.create_task(self.bot_stats_updater())

        self.loop.create_task(self.premium_updater())
        self.loop.create_task(self.cleanup())


class Main:
    def __init__(self, loop):
        self.loop = loop
        self.instances = []
        self.bot = None
        self.shard_count = None

    def dead_process_handler(self, result):
        instance = result.result()
        print(
            f"[Cluster {instance.id}] The cluster exited with code {instance._process.returncode}."
        )

        if instance._process.returncode in [0, -15]:
            print(f"[Cluster {instance.id}] The cluster stopped gracefully.")
            return

        print(f"[Cluster {instance.id}] The cluster is restarting.")
        instance.loop.create_task(instance.start())

    async def user_select_handler(self, body):
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO account VALUES ($1, TRUE, $2) ON CONFLICT (identifier) DO UPDATE SET "
                "token=$2",
                int(body["id"]),
                body["token"],
            )

        user_select = await self.bot.state.get(f"user_select:{body['id']}")
        if not user_select:
            return

        await self.bot.state.delete(f"user_select:{body['id']}")

        channel = tools.create_fake_channel(self.bot, user_select["message"]["channel_id"])
        message = Message(state=self.bot.state, channel=channel, data=user_select["message"])
        msg = Message(state=self.bot.state, channel=channel, data=user_select["msg"])

        await tools.select_guild(self.bot, message, msg)

    async def handler(self, request):
        if request.method == "GET" and request.path == "/healthcheck":
            return web.Response(body='{"status":"Ok"}', content_type="application/json")
        elif request.method == "GET" and request.path == "/restart":
            for instance in self.instances:
                self.loop.create_task(instance.restart())
            return web.Response(body='{"status":"Ok"}', content_type="application/json")
        elif request.method == "POST" and request.path == "/success":
            body = await request.json()
            self.loop.create_task(self.user_select_handler(body))
            return web.Response(body='{"status":"Ok"}', content_type="application/json")

    def write_targets(self):
        data = []

        data.append({"labels": {"cluster": "0"}, "targets": ["localhost:6100"]})
        for i in range(1, len(self.instances) + 1):
            data.append({"labels": {"cluster": str(i)}, "targets": [f"localhost:{6100 + i}"]})

        with open("targets.json", "w") as file:
            json.dump(data, file, indent=2)

    async def launch(self):
        print(f"[Cluster Manager] Starting a total of {config.BOT_CLUSTERS} clusters.")

        self.bot = ModMail(cluster_id=0, cluster_count=int(config.BOT_CLUSTERS))
        await self.bot.start(worker=False)

        self.bot.id = (await self.bot.real_user()).id
        self.bot.state.id = self.bot.id

        for i in range(int(config.BOT_CLUSTERS)):
            self.instances.append(Instance(i + 1, loop=self.loop, main=self))

        self.write_targets()

        scheduler = Scheduler(loop=self.loop, bot=self.bot)
        loop.create_task(scheduler.launch())

        server = web.Server(self.handler)
        runner = web.ServerRunner(server)
        await runner.setup()
        site = web.TCPSite(runner, config.BOT_API_HOST, int(config.BOT_API_PORT))
        await site.start()


config = Config().load()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
main = Main(loop=loop)
loop.create_task(main.launch())

try:
    loop.run_forever()
except KeyboardInterrupt:

    def shutdown_handler(_loop, context):
        if "exception" not in context or not isinstance(
            context["exception"], asyncio.CancelledError
        ):
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

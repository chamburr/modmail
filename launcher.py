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

import config

from classes.bot import ModMail
from classes.channel import DMChannel
from classes.embed import ErrorEmbed
from classes.message import Message
from utils.tools import select_guild


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
            f"{sys.executable} \"{Path.cwd() / 'main.py'}\" {self.id} {config.clusters} "
            f"{self.main.bot_id}",
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
    def __init__(self, loop, main):
        self.loop = loop
        self.pool = main.bot.pool
        self.state = main.bot.state
        self.http = main.bot.http
        self.bot_id = main.bot_id
        self.shard_count = main.shard_count
        self.session = aiohttp.ClientSession()

    async def premium_updater(self):
        while True:
            async with self.pool.acquire() as conn:
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
            if not self.bot_id and not self.shard_count:
                continue

            guilds = await self.state.scard("guild_keys")

            await self.session.post(
                f"https://top.gg/api/bots/{self.bot_id}/stats",
                data=orjson.dumps({"server_count": guilds, "shard_count": self.shard_count}),
                headers={"Authorization": config.topgg_token, "Content-Type": "application/json"},
            )

            await self.session.post(
                f"https://discord.bots.gg/api/v1/bots/{self.bot_id}/stats",
                data=orjson.dumps({"guildCount": guilds, "shardCount": self.shard_count}),
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

            await self.state.set(
                "bot_stats",
                {
                    "version": "3.0.0",
                    "started": await self.state.get("gateway_started"),
                    "shards": await self.state.get("gateway_shards"),
                    "guilds": guilds,
                    "roles": await self.state.scard("role_keys"),
                    "channels": await self.state.scard("channel_keys"),
                    "members": await self.state.scard("member_keys"),
                },
            )

            await asyncio.sleep(900)

    async def cleanup(self):
        while True:
            for menu in await self.state.smembers("reaction_menus"):

                if menu["end"] > int(time.time()):
                    continue

                if menu["kind"] == "paginator":
                    try:
                        await self.http.clear_reactions(menu["channel"], menu["message"])
                    except discord.Forbidden:
                        for reaction in ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]:
                            try:
                                await self.http.remove_own_reaction(
                                    menu["channel"], menu["message"], reaction
                                )
                            except discord.NotFound:
                                pass
                elif menu["kind"] == "confirmation":
                    for reaction in ["✅", "🔁", "❌"]:
                        await self.http.remove_own_reaction(
                            menu["channel"], menu["message"], reaction
                        )

                    await self.http.edit_message(
                        menu["channel"],
                        menu["message"],
                        ErrorEmbed("Time out. You did not choose anything.").to_dict(),
                    )
                elif menu["kind"] == "selection":
                    await self.http.remove_own_reaction(menu["channel"], menu["message"], "◀")
                    await self.http.remove_own_reaction(menu["channel"], menu["message"], "▶")

                    for reaction in ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"]:
                        try:
                            await self.http.remove_own_reaction(
                                menu["channel"], menu["message"], reaction
                            )
                        except discord.NotFound:
                            pass

                    await self.http.edit_message(
                        menu["channel"],
                        menu["message"],
                        ErrorEmbed("Time out. You did not choose anything.").to_dict(),
                    )

                await self.state.srem("reaction_menus", menu)

            await asyncio.sleep(10)

    async def launch(self):
        async with self.pool.acquire() as conn:
            data = await conn.fetch("SELECT guild, prefix FROM data")
            bans = await conn.fetch("SELECT identifier, category FROM ban")

        if len(data) >= 1:
            await self.state.set(
                [y for x in data for y in (f"prefix:{x[0]}", "" if x[1] is None else x[1])]
            )

        if len([x[0] for x in bans if x[1] == 0]) >= 1:
            await self.state.sadd("banned_users", *[x[0] for x in bans if x[1] == 0])

        if len([x[0] for x in bans if x[1] == 1]) >= 1:
            await self.state.sadd("banned_guilds", *[x[0] for x in bans if x[1] == 1])

        if config.testing is False:
            self.loop.create_task(self.bot_stats_updater())

        self.loop.create_task(self.premium_updater())
        self.loop.create_task(self.cleanup())


class Main:
    def __init__(self, loop):
        self.loop = loop
        self.instances = []
        self.bot = None
        self.bot_id = None
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

    async def handler(self, request):
        if request.path == "/healthcheck":
            return web.Response(body='{"status":"Ok"}', content_type="application/json")
        elif request.path == "/restart":
            for instance in self.instances:
                self.loop.create_task(instance.restart())
            return web.Response(body='{"status":"Restarting"}', content_type="application/json")
        elif request.path.startswith("/success"):
            user_id = request.path[8:]
            login_message = self.bot.state.get(f"login_message:{user_id}")
            user_message = self.bot.state.get(f"user_message:{user_id}")

            if login_message is None or user_message is None:
                return

            channel = DMChannel(
                me=self.bot.user, state=self.bot.state, data={"id": login_message["id"]}
            )
            login_message = Message(state=self.bot.state, channel=channel, data=login_message)
            user_message = Message(state=self.bot.state, channel=channel, data=user_message)

            await select_guild(self.bot, user_message, login_message)

    def write_targets(self, clusters):
        data = []

        for i in range(len(clusters)):
            data.append({"labels": {"cluster": str(i)}, "targets": [f"localhost:{6000 + i}"]})

        with open("targets.json", "w") as file:
            json.dump(data, file, indent=2)

    async def launch(self):
        print(f"[Cluster Manager] Starting a total of {config.clusters} clusters.")

        self.bot = ModMail(command_prefix=None)
        await self.bot.start(True)

        async with self.bot.pool.acquire() as conn:
            exists = await conn.fetchrow(
                "SELECT EXISTS (SELECT relname FROM pg_class WHERE relname = 'data')"
            )
            if exists[0] is False:
                with open("schema.sql", "r") as file:
                    await conn.execute(file.read())

        self.bot_id = (await self.bot.real_user()).id
        self.shard_count = int(await self.bot.state.get("gateway_shards"))

        for i in range(config.clusters):
            self.instances.append(Instance(i + 1, loop=self.loop, main=self))

        self.write_targets(self.instances)

        scheduler = Scheduler(loop=self.loop, main=self)
        loop.create_task(scheduler.launch())

        server = web.Server(self.handler)
        runner = web.ServerRunner(server)
        await runner.setup()
        site = web.TCPSite(runner, config.http_api["host"], config.http_api["port"])
        await site.start()


loop = asyncio.get_event_loop()
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

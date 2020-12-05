import asyncio
import datetime
import json
import logging

from importlib import reload as importlib_reload
from uuid import uuid4

import discord
import discord.utils as utils

from async_timeout import timeout
from discord.ext import commands

from utils.eval import evaluate as _evaluate

log = logging.getLogger(__name__)


class DictToObj:
    def __init__(self, **entries):
        for key, value in entries.items():
            if isinstance(value, dict):
                self.__dict__[key] = DictToObj(**value)
            elif isinstance(value, (tuple, list)):
                self.__dict__[key] = [DictToObj(**x) for x in value]
            else:
                self.__dict__[key] = value


class Communication(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ipc_channel = self.bot.config.ipc_channel
        self.router = None
        self._messages = dict()
        self.bot.loop.create_task(self.register_sub())

    def cog_unload(self):
        self.bot.loop.create_task(self.unregister_sub())

    async def register_sub(self):
        if not bytes(self.ipc_channel, "utf-8") in self.bot.redis.pubsub_channels:
            await self.bot.redis.execute_pubsub("SUBSCRIBE", self.ipc_channel)
        self.router = self.bot.loop.create_task(self.event_handler())

    async def unregister_sub(self):
        if self.router and not self.router.cancelled:
            self.router.cancel()
        await self.bot.redis.execute_pubsub("UNSUBSCRIBE", self.ipc_channel)

    async def run_action(self, payload, args):
        try:
            if args is True:
                await getattr(self, payload["action"])(**json.loads(payload["args"]), command_id=payload["command_id"])
            else:
                await getattr(self, payload["action"])(command_id=payload["command_id"])
        except Exception as e:
            new_payload = {
                "error": True,
                "output": f"```{type(e).__name__} - {e}```",
                "command_id": payload["command_id"],
            }
            await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(new_payload))

    async def event_handler(self):
        channel = self.bot.redis.pubsub_channels[bytes(self.ipc_channel, "utf-8")]
        while await channel.wait_message():
            payload = await channel.get_json(encoding="utf-8")
            if payload.get("action"):
                if payload.get("scope") != "bot":
                    continue
                if payload.get("args"):
                    self.bot.loop.create_task(self.run_action(payload, True))
                else:
                    self.bot.loop.create_task(self.run_action(payload, False))
            if payload.get("output") and payload["command_id"] in self._messages:
                self._messages[payload["command_id"]].append(payload["output"])

    def serialise_value(self, value):
        if isinstance(value, (bool, str, float, int)) or value is None:
            return value
        elif isinstance(value, datetime.datetime):
            return value.timestamp()
        elif isinstance(value, discord.enums.Enum):
            return value.__str__
        elif isinstance(value, (tuple, list)):
            return [self.serialise_value(x) for x in value]
        else:
            return str(value)

    def to_dict(self, cls, attrs=None, default=True):
        if attrs is None:
            attrs = []
        if default is True:
            attrs.append("name")
            attrs.append("id")
        result = {}
        for attr in attrs:
            value = getattr(cls, attr)
            result[attr] = self.serialise_value(value)
        return result

    async def guild_count(self, command_id):
        payload = {"output": len(self.bot.guilds), "command_id": command_id}
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def channel_count(self, command_id):
        payload = {
            "output": sum([len(guild.channels) for guild in self.bot.guilds]),
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def user_count(self, command_id):
        payload = {"output": len(self.bot.users), "command_id": command_id}
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def get_user(self, user_id, command_id):
        user = self.bot.get_user(user_id)
        if not user:
            return
        payload = {
            "output": self.to_dict(user),
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def get_user_premium(self, user_id, command_id):
        guild = self.bot.get_guild(self.bot.config.main_server)
        if not guild:
            return
        member = guild.get_member(user_id)
        if not member:
            return
        if user_id in self.bot.config.admins or user_id in self.bot.config.owners:
            amount = 1000
        elif utils.get(member.roles, id=self.bot.config.premium5):
            amount = 5
        elif utils.get(member.roles, id=self.bot.config.premium3):
            amount = 3
        elif utils.get(member.roles, id=self.bot.config.premium1):
            amount = 1
        else:
            amount = 0
        payload = {"output": amount, "command_id": command_id}
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def get_user_guilds(self, user_id, command_id):
        if not self.bot.get_user(user_id):
            return
        guilds = []
        for guild in self.bot.guilds:
            if not guild.get_member(user_id):
                continue
            guild_dict = self.to_dict(guild, ["icon_url", "member_count"])
            guild_dict["text_channels"] = [self.to_dict(x, ["topic"]) for x in guild.text_channels]
            guilds.append(guild_dict)
        payload = {
            "output": guilds,
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def get_status(self, command_id):
        payload = {
            "output": {
                self.bot.cluster: {
                    "ready": self.bot.is_ready(),
                    "shards": ", ".join([str(x) for x in self.bot.shard_ids]),
                    "latency": round(self.bot.latency * 1000, 2),
                    "uptime": self.bot.uptime.total_seconds(),
                },
            },
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def get_guild(self, guild_id, command_id):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        guild_dict = self.to_dict(guild, ["icon_url"])
        guild_dict["text_channels"] = [self.to_dict(x, ["topic"]) for x in guild.text_channels]
        payload = {
            "output": guild_dict,
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def get_guild_member(self, guild_id, member_id, command_id):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        member = guild.get_member(member_id)
        if not member:
            return
        payload = {"output": self.to_dict(member), "command_id": command_id}
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def get_guild_channel(self, guild_id, channel_id, command_id):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        channel = guild.get_channel(channel_id)
        if not channel:
            return
        payload = {"output": self.to_dict(channel), "command_id": command_id}
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def get_top_guilds(self, count, command_id):
        guilds = sorted(self.bot.guilds, key=lambda x: x.member_count, reverse=True)[:count]
        payload = {
            "output": [self.to_dict(guild, ["member_count"]) for guild in guilds],
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def find_guild(self, name, command_id):
        payload = {
            "output": [
                self.to_dict(guild, ["member_count"])
                for guild in self.bot.guilds
                if guild.name.lower().count(name.lower()) > 0
            ],
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def invite_guild(self, guild_id, command_id):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        try:
            invite = (await guild.invites())[0]
        except (IndexError, discord.Forbidden):
            try:
                invite = await guild.text_channels[0].create_invite(max_age=120)
            except discord.Forbidden:
                return
        payload = {"output": self.to_dict(invite, ["code"], False), "command_id": command_id}
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def leave_guild(self, guild_id, command_id):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        await guild.leave()
        payload = {
            "output": "Success",
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def evaluate(self, code, command_id):
        payload = {"output": await _evaluate(self.bot, code), "command_id": command_id}
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def unload_extension(self, cog, command_id):
        self.bot.unload_extension("cogs." + cog)
        payload = {
            "output": "Success",
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def load_extension(self, cog, command_id):
        self.bot.load_extension("cogs." + cog)
        payload = {
            "output": "Success",
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def reload_extension(self, cog, command_id):
        self.bot.unload_extension("cogs." + cog)
        self.bot.load_extension("cogs." + cog)
        payload = {
            "output": "Success",
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def reload_import(self, lib, command_id):
        importlib_reload(getattr(self.bot, lib))
        payload = {
            "output": "Success",
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def handler(self, action, expected_count, args=None, _timeout=2, scope="bot", cluster=None):
        command_id = f"{uuid4()}"
        self._messages[command_id] = []
        payload = {"scope": scope, "action": action, "command_id": command_id}
        if cluster:
            payload["id"] = cluster
        if args:
            payload["args"] = json.dumps(args)
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))
        try:
            async with timeout(_timeout):
                while len(self._messages[command_id]) < abs(expected_count):
                    await asyncio.sleep(0.1)
        except asyncio.TimeoutError:
            pass
        msg = self._messages.pop(command_id, None)
        if msg is None:
            return None
        new_msg = []
        for entry in msg:
            if isinstance(entry, (list, tuple)):
                new_msg.append([DictToObj(**x) if isinstance(x, dict) else x for x in entry])
            elif isinstance(entry, dict):
                new_msg.append(DictToObj(**entry))
            else:
                new_msg.append(entry)
        if expected_count == -1:
            if len(new_msg) == 0:
                return None
            else:
                return new_msg[0]
        return new_msg


def setup(bot):
    bot.add_cog(Communication(bot))

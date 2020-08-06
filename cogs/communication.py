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


class Communication(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ipc_channel = self.bot.ipc_channel
        self.router = None
        bot.loop.create_task(self.register_sub())
        self._messages = dict()

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
            log.info(json.dumps(new_payload))
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

    def to_dict(self, cls, ignore=None, attrs=None):
        if ignore is None:
            ignore = []
        if attrs is None:
            attrs = []
        result = {}
        attrs.extend(cls.__slots__)
        for attr in attrs:
            if attr in ignore or attr.startswith("_"):
                continue
            result[attr] = getattr(cls, attr)
            if isinstance(result[attr], datetime.datetime):
                result[attr] = result[attr].timestamp()
            elif isinstance(result[attr], discord.enums.Enum):
                result[attr] = result[attr].__str__
            elif hasattr(result[attr], "__slots__"):
                if not [slot for slot in getattr(result[attr], "__slots__") if not slot.startswith("_")]:
                    result[attr] = str(result[attr])
                else:
                    result[attr] = self.to_dict(result[attr], ignore)
            elif isinstance(result[attr], list) or isinstance(result[attr], tuple):
                new_list = []
                for element in result[attr]:
                    if hasattr(element, "__slots__"):
                        new_list.append(self.to_dict(element, ignore))
                    else:
                        new_list.append(element)
                result[attr] = new_list
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
        if not self.bot.get_user(user_id):
            return
        payload = {
            "output": self.to_dict(self.bot.get_user(user_id), ["user"]),
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
        payload = {
            "output": [
                self.to_dict(guild, ["guild"], ["text_channels", "icon_url", "default_role"])
                for guild in self.bot.guilds
                if guild.get_member(user_id) is not None
            ],
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def get_status(self, command_id):
        payload = {
            "output": {
                self.bot.cluster: {
                    "ready": self.bot.is_ready(),
                    "shards": self.bot.shard_ids.join(", "),
                    "latency": round(self.bot.latency * 1000, 2),
                    "uptime": self.bot.uptime,
                },
            },
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def get_guild(self, guild_id, command_id):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        payload = {
            "output": self.to_dict(guild, ["guild"], ["text_channels", "icon_url", "default_role"]),
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
        payload = {"output": self.to_dict(member, ["guild", "member"]), "command_id": command_id}
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def get_guild_channel(self, guild_id, channel_id, command_id):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        channel = guild.get_channel(channel_id)
        if not channel:
            return
        payload = {"output": self.to_dict(channel, ["channel", "guild"]), "command_id": command_id}
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def get_top_guilds(self, command_id):
        guilds = sorted(self.bot.guilds, key=lambda x: x.member_count, reverse=True)[:15]
        payload = {
            "output": [self.to_dict(guild, ["guild"], ["member_count"]) for guild in guilds],
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def find_guild(self, name, command_id):
        guilds = []
        for guild in self.bot.guilds:
            if guild.name.lower().count(name.lower()) > 0:
                guilds.append(f"{guild.name} `{guild.id}`")
        payload = {"output": guilds, "command_id": command_id}
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
        payload = {"output": self.to_dict(invite, ["invite", "guild"]), "command_id": command_id}
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

    async def reload_import(self, lib, command_id):
        importlib_reload(getattr(self.bot, lib))
        payload = {
            "output": "Success",
            "command_id": command_id,
        }
        await self.bot.redis.execute("PUBLISH", self.ipc_channel, json.dumps(payload))

    async def handler(self, action, expected_count, args=None, _timeout=1, scope="bot", cluster=None):
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
                while len(self._messages[command_id]) < expected_count:
                    await asyncio.sleep(0.05)
        except asyncio.TimeoutError:
            pass
        return self._messages.pop(command_id, None)


def setup(bot):
    bot.add_cog(Communication(bot))

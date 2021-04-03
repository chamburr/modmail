import logging
import time

import aiohttp

from discord.user import User

from classes.channel import DMChannel

log = logging.getLogger(__name__)


def create_fake_user(user_id):
    return User(
        state=None,
        data={
            "username": "",
            "id": str(user_id),
            "discriminator": "",
            "avatar": "",
        },
    )


def upgrade_payload(data):
    if data.get("permission_overwrites"):
        data["permission_overwrites"] = [
            {
                "id": x["id"],
                "type": "role" if x["type"] == 0 else "member",
                "allow": int(x["allow"]),
                "allow_new": x["allow"],
                "deny": int(x["deny"]),
                "deny_new": x["deny"],
            }
            for x in data["permission_overwrites"]
        ]

    if data.get("permissions"):
        data["permissions_new"] = data["permissions"]
        data["permissions"] = int(data["permissions"])

    return data


async def create_paginator(bot, ctx, pages):
    msg = await ctx.send(embed=pages[0])

    for reaction in ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]:
        await msg.add_reaction(reaction)

    await bot.state.sadd(
        "reaction_menus",
        {
            "kind": "paginator",
            "channel": msg.channel.id,
            "message": msg.id,
            "end": int(time.time()) + 180,
            "data": {
                "page": 0,
                "all_pages": [page.to_dict() for page in pages],
            },
        },
    )


async def get_reaction_menu(bot, payload, kind):
    for menu in await bot.state.smembers("reaction_menus"):
        if menu["channel"] == payload.channel_id and menu["message"] == payload.message_id and menu["kind"] == kind:
            channel = DMChannel(me=bot.user, state=bot.state, data={"id": menu["channel"]})
            message = channel.get_partial_message(menu["message"])

            return menu, channel, message

    return None, None, None


async def get_data(bot, guild):
    async with bot.pool.acquire() as conn:
        res = await conn.fetchrow("SELECT * FROM data WHERE guild=$1", guild)
        if not res:
            res = await conn.fetchrow(
                "INSERT INTO data VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING *",
                guild,
                None,
                None,
                [],
                None,
                None,
                None,
                False,
                [],
                [],
                False,
            )

    return res


async def get_guild_prefix(bot, guild):
    if not guild:
        return bot.config.default_prefix

    prefix = await bot.state.get(f"prefix:{guild.id}")
    if prefix == "":
        return bot.config.default_prefix
    elif prefix is not None:
        return prefix

    async with bot.pool.acquire() as conn:
        res = await conn.fetchrow("SELECT prefix FROM data WHERE guild=$1", guild.id)

    if res and res[0]:
        await bot.state.set(f"prefix:{guild.id}", res[0])
        return res[0]

    await bot.state.set(f"prefix:{guild.id}", "")
    return bot.config.default_prefix


async def get_user_settings(bot, user):
    async with bot.pool.acquire() as conn:
        return await conn.fetchrow("SELECT confirmation FROM preference WHERE identifier=$1", user)


async def get_premium_slots(bot, user):
    if user in bot.config.owners + bot.config.admins:
        return 1000

    guild = await bot.get_guild(bot.config.main_server)
    if guild:
        member = await guild.get_member(user)
        if member:
            if bot.config.premium5 in member._roles:
                return 5
            elif bot.config.premium3 in member._roles:
                return 3
            elif bot.config.premium1 in member._roles:
                return 1

    async with bot.pool.acquire() as conn:
        res = await conn.fetchrow("SELECT guild FROM premium WHERE identifier=$1", user)

    if res:
        return 1

    return 0


async def remove_premium(bot, guild):
    async with bot.pool.acquire() as conn:
        await conn.execute(
            "UPDATE data SET welcome=$1, goodbye=$2, loggingplus=$3 WHERE guild=$4",
            None,
            None,
            False,
            guild,
        )
        await conn.execute("DELETE FROM snippet WHERE guild=$1", guild)


async def is_user_banned(bot, user):
    return await bot.state.sismember("banned_users", user.id)


async def is_guild_banned(bot, guild):
    return await bot.state.sismember("banned_guilds", guild.id)

async def get_user_guilds(bot, member):
    headers = {
        "User-Id": member.id,
        "User-Username": member.name,
        "User-Discriminator": member.discriminator,
        "User-Avatar": member.avatar if member.avatar else ""
    }

    resp = (await bot.session.get(f"{bot.config.base_uri}/api/users/@me/guilds", headers=headers))

    if resp.status == 400:
        return []

    resp = resp.json()

    return [x["id"] for x in resp]


def is_modmail_channel(channel, user_id=None):
    return (
        channel.topic
        and channel.topic.startswith("ModMail Channel ")
        and channel.topic.replace("ModMail Channel ", "").split(" ")[0].isdigit()
        and channel.topic.replace("ModMail Channel ", "").split(" ")[1].isdigit()
        and (channel.topic.replace("ModMail Channel ", "").split(" ")[0] == str(user_id) if user_id else True)
    )


def get_modmail_user(channel):
    return create_fake_user(channel.topic.replace("ModMail Channel ", "").split(" ")[0])


def get_modmail_channel(bot, channel):
    return DMChannel(
        me=bot.user,
        state=bot.state,
        data={"id": int(channel.topic.replace("ModMail Channel ", "").split(" ")[1])},
    )


def perm_format(perm):
    return perm.replace("_", " ").replace("guild", "server").title()


def tag_format(message, author):
    tags = {
        "{username}": author.name,
        "{usertag}": author.discriminator,
        "{userid}": str(author.id),
        "{usermention}": author.mention,
    }

    for tag, val in tags.items():
        message = message.replace(tag, val)

    if len(message) > 2048:
        return message[:2045] + "..."

    return message

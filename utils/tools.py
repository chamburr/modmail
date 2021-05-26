import logging
import time

import aiohttp
import discord

from discord.user import User

from classes.message import Message
from classes.channel import DMChannel
from classes.embed import Embed, ErrorEmbed

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


def create_fake_message(bot, channel, message_id):
    return Message(
        state=bot.state,
        channel=channel,
        data={
            "id": message_id,
            "attachments": [],
            "embeds": [],
            "edited_timestamp": 0,
            "type": 0,
            "pinned": False,
            "mention_everyone": False,
            "tts": False,
            "content": "",
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
    if len(pages) == 1:
        embed = pages[0]
        embed.set_footer(discord.Embed.Empty)
        await ctx.send(embed)
        return

    msg = await ctx.send(pages[0])

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
        if (
            menu["channel"] == payload.channel_id
            and menu["message"] == payload.message_id
            and menu["kind"] == kind
        ):
            channel = DMChannel(me=bot.user, state=bot.state, data={"id": menu["channel"]})
            message = create_fake_message(bot, channel, menu["message"])

            return menu, channel, message

    return None, None, None


async def get_data(bot, guild):
    async with bot.pool.acquire() as conn:
        res = await conn.fetchrow("SELECT * FROM data WHERE guild=$1", guild)
        if res:
            return res

        return await conn.fetchrow(
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


async def get_guild_prefix(bot, guild):
    if not guild:
        return bot.config.DEFAULT_PREFIX

    prefix = await bot.state.get(f"prefix:{guild.id}")
    if prefix == "":
        return bot.config.DEFAULT_PREFIX
    elif prefix is not None:
        return prefix

    async with bot.pool.acquire() as conn:
        res = await conn.fetchrow("SELECT prefix FROM data WHERE guild=$1", guild.id)

    if res and res[0]:
        await bot.state.set(f"prefix:{guild.id}", res[0])
        return res[0]

    await bot.state.set(f"prefix:{guild.id}", "")
    return bot.config.DEFAULT_PREFIX


async def get_user_settings(bot, user):
    async with bot.pool.acquire() as conn:
        return await conn.fetchrow("SELECT confirmation FROM preference WHERE identifier=$1", user)


async def get_premium_slots(bot, user):
    if str(user) in bot.config.OWNER_USERS.split(",") + bot.config.ADMIN_USERS.split(","):
        return 1000

    guild = await bot.get_guild(int(bot.config.MAIN_SERVER))
    if guild:
        member = await guild.get_member(user)
        if member:
            if int(bot.config.PREMIUM5_ROLE) in member._roles:
                return 5
            elif int(bot.config.PREMIUM3_ROLE) in member._roles:
                return 3
            elif int(bot.config.PREMIUM1_ROLE) in member._roles:
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


async def get_user_guilds(state, member):
    user_guilds = await state.get(f"user_guilds:{member.id}")
    if user_guilds is not None:
        return user_guilds

    token = await state.get(f"user_token:{member.id}")
    if token is None:
        return None

    async with aiohttp.ClientSession() as session, session.get(
        "https://discord.com/api/v9/users/@me/guilds",
        headers={"Authorization": f"Bearer {token}"},
    ) as req:
        response = req.json()

    await state.set(f"user_guilds:{member.id}", response)
    await state.expire(f"user_guilds:{member.id}", 10)
    return response


async def select_guild(bot, message, msg=None):
    guilds = {}

    user_guilds = await get_user_guilds(bot.state, message.author)
    if user_guilds is None:
        embed = Embed(f"Please login at [this link](https://{bot.config.BASE_URI}/login).")
        if msg:
            msg = await msg.edit(embed)
        else:
            msg = await message.channel.send(embed)

        await bot.state.set(
            f"user_select:{message.author.id}",
            {
                "message": message._data,
                "msg": msg._data,
            },
        )

        return

    for guild in user_guilds:
        guild = await bot.get_guild(int(guild))

        channel = None
        for text_channel in await guild.text_channels():
            if is_modmail_channel(text_channel, message.author.id):
                channel = text_channel

        if not channel:
            guilds[str(guild.id)] = (guild.name, False)
        else:
            guilds[str(guild.id)] = (guild.name, True)

    if len(guilds) == 0:
        await message.channel.send(
            ErrorEmbed("Oops, something strange happened. No server was found.")
        )
        return

    embeds = []

    for chunk in [list(guilds.items())[i : i + 10] for i in range(0, len(guilds), 10)]:
        embed = Embed(
            "Select Server",
            "Please select the server you want to send this message to. You can do so by reacting "
            "with the corresponding emote.",
        )
        embed.set_footer("Use the reactions to flip pages.")

        for guild, value in chunk:
            embed.add_field(
                f"{len(embed.fields) + 1}: {value[0]}",
                f"{'Create a new ticket.' if value[1] is False else 'Existing ticket.'}\n"
                f"Server ID: {guild}",
            )

        embeds.append(embed)

    if msg:
        msg = await msg.edit(embeds[0])
    else:
        msg = await message.channel.send(embeds[0])

    await msg.add_reaction("◀")
    await msg.add_reaction("▶")
    for reaction in ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"][
        : len(embeds[0].fields)
    ]:
        await msg.add_reaction(reaction)

    await bot.state.sadd(
        "reaction_menus",
        {
            "kind": "selection",
            "channel": msg.channel.id,
            "message": msg.id,
            "end": int(time.time()) + 180,
            "data": {
                "msg": message._data,
                "page": 0,
                "all_pages": [embed.to_dict() for embed in embeds],
            },
        },
    )


def is_modmail_channel(channel, user_id=None):
    return (
        channel.topic
        and channel.topic.startswith("ModMail Channel ")
        and channel.topic.replace("ModMail Channel ", "").split(" ")[0].isdigit()
        and channel.topic.replace("ModMail Channel ", "").split(" ")[1].isdigit()
        and (
            channel.topic.replace("ModMail Channel ", "").split(" ")[0] == str(user_id)
            if user_id
            else True
        )
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

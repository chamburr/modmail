import logging
import time

import discord

from discord.http import Route
from discord.user import User

from classes.channel import DMChannel
from classes.embed import Embed, ErrorEmbed
from classes.http import HTTPClient
from classes.message import Message

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


def create_fake_channel(bot, channel_id):
    return DMChannel(me=bot.user, state=bot.state, data={"id": channel_id})


def create_fake_message(bot, channel, message_id):
    return Message(
        state=bot.state,
        channel=channel,
        data={
            "id": message_id,
            "channel_id": channel.id,
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


async def create_paginator(bot, ctx, pages):
    if len(pages) == 1:
        embed = pages[0]
        embed.set_footer(discord.Embed.Empty)
        await ctx.send(embed)
        return

    msg = await ctx.send(pages[0])

    for reaction in ["⏮️", "◀️", "⏹️", "▶️", "⏭️"]:
        await msg.add_reaction(reaction)

    await bot.state.set(
        f"reaction_menu:{msg.channel.id}:{msg.id}",
        {
            "kind": "paginator",
            "end": int(time.time()) + 180,
            "data": {
                "page": 0,
                "all_pages": [page.to_dict() for page in pages],
            },
        },
    )
    await bot.state.sadd("reaction_menu_keys", f"reaction_menu:{msg.channel.id}:{msg.id}")


async def select_guild(bot, message, msg):
    guilds = {}

    user_guilds = await get_user_guilds(bot, message.author)
    if user_guilds is None:
        embed = Embed(
            f"Please [click here]({bot.config.BASE_URI}/login?redirect=/authorized) to verify. "
            "This will allow the bot to see your servers and is required for the bot to function. "
            "Then, close the page and return back here."
        )
        await msg.edit(embed)

        await bot.state.set(
            f"user_select:{message.author.id}",
            {
                "message": message._data,
                "msg": msg._data,
            },
        )

        return

    for guild in user_guilds:
        guild = await bot.get_guild(guild)
        if guild is None:
            continue

        channel = None
        for text_channel in await guild.text_channels():
            if is_modmail_channel(text_channel, message.author.id):
                channel = text_channel

        if not channel:
            guilds[str(guild.id)] = (guild.name, False)
        else:
            guilds[str(guild.id)] = (guild.name, True)

    if len(guilds) == 0:
        await message.channel.send(ErrorEmbed("Oops, something strange happened. No server found."))
        return

    embeds = []

    for chunk in [list(guilds.items())[i : i + 10] for i in range(0, len(guilds), 10)]:
        embed = Embed(
            "Select Server",
            "Please select the server you want to send this message to. You can do so by reacting "
            "with the corresponding emote.",
        )

        if len(guilds) > 10:
            embed.set_footer("Use the reactions to flip pages.")

        for guild, value in chunk:
            embed.add_field(
                f"{len(embed.fields) + 1}: {value[0]}",
                f"{'Create a new ticket.' if value[1] is False else 'Existing ticket.'}\n"
                f"Server ID: {guild}",
            )

        embeds.append(embed)

    await msg.edit(embeds[0])

    if len(guilds) > 10:
        await msg.add_reaction("◀️")
        await msg.add_reaction("▶️")

    for reaction in ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"][
        : len(embeds[0].fields)
    ]:
        await msg.add_reaction(reaction)

    await bot.state.set(
        f"reaction_menu:{msg.channel.id}:{msg.id}",
        {
            "kind": "selection",
            "end": int(time.time()) + 180,
            "data": {
                "msg": message._data,
                "page": 0,
                "all_pages": [embed.to_dict() for embed in embeds],
            },
        },
    )
    await bot.state.sadd("reaction_menu_keys", f"reaction_menu:{msg.channel.id}:{msg.id}")


async def get_reaction_menu(bot, payload, kind):
    menu = await bot.state.get(f"reaction_menu:{payload.channel_id}:{payload.message_id}")
    if menu and menu["kind"] == kind:
        channel = create_fake_channel(bot, payload.channel_id)
        message = create_fake_message(bot, channel, payload.message_id)

        return menu, channel, message

    return None, None, None


async def get_data(bot, guild):
    async with bot.pool.acquire() as conn:
        res = await conn.fetchrow("SELECT * FROM data WHERE guild=$1", guild)
        if res:
            return res

        return await conn.fetchrow(
            "INSERT INTO data VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13) "
            "RETURNING *",
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
            False,
            None,
        )


async def get_guild_prefix(bot, guild):
    if not guild:
        return bot.config.DEFAULT_PREFIX

    prefix = await bot.state.get(f"prefix:{guild.id}", False)
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
        return await conn.fetchrow("SELECT confirmation FROM account WHERE identifier=$1", user)


async def get_user_guilds(bot, member):
    user_guilds = await bot.state.get(f"user_guilds:{member.id}")
    if user_guilds is not None:
        return [int(guild) for guild in user_guilds]

    token = await bot.state.get(f"user_token:{member.id}", False)
    if token is None:
        async with bot.pool.acquire() as conn:
            res = await conn.fetchrow("SELECT token FROM account WHERE identifier=$1", member.id)

        if not res or not res[0]:
            return None

        async with bot.session.post(
            f"{Route.BASE}/oauth2/token",
            data={
                "client_id": bot.config.BOT_CLIENT_ID,
                "client_secret": bot.config.BOT_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": res[0],
            },
        ) as response:
            if response.status != 200:
                async with bot.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE account SET token=NULL WHERE identifier=$1",
                        member.id,
                    )
                return None

            response = await response.json()

        token = response["access_token"]
        await bot.state.set(f"user_token:{member.id}", token)
        await bot.state.expire(f"user_token:{member.id}", response["expires_in"])

        async with bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE account SET token=$1 WHERE identifier=$2",
                response["refresh_token"],
                member.id,
            )

    http = HTTPClient()
    http._HTTPClient__session = bot.session
    http._token(f"Bearer {token}", bot=False)

    try:
        guilds = [guild["id"] for guild in await http.get_guilds(200)]
    except discord.HTTPException:
        await bot.state.delete(f"user_token:{member.id}")
        return await get_user_guilds(bot, member)

    await bot.state.set(f"user_guilds:{member.id}", guilds)
    await bot.state.expire(f"user_guilds:{member.id}", 10)

    return [int(guild) for guild in guilds]


async def get_premium_slots(bot, user):
    if str(user) in bot.config.OWNER_USERS.split(",") + bot.config.ADMIN_USERS.split(","):
        return 1000

    guild = await bot.get_guild(int(bot.config.MAIN_SERVER))
    if guild:
        member = await guild.fetch_member(user)
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


def is_modmail_channel(channel, user_id=None):
    if not getattr(channel, "topic", None) or not channel.topic.startswith("ModMail Channel "):
        return False

    parts = channel.topic.replace("ModMail Channel ", "").split(" ")
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return False

    if user_id and parts[0] != str(user_id):
        return False

    return True


def get_modmail_user(channel):
    return create_fake_user(channel.topic.replace("ModMail Channel ", "").split(" ")[0])


def get_modmail_channel(bot, channel):
    return create_fake_channel(bot, channel.topic.replace("ModMail Channel ", "").split(" ")[1])


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

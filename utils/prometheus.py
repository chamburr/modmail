import asyncio

import prometheus_client as prom

latency_counter = prom.Gauge("modmail_latency", "The average latency for shards on this cluster")
events_counter = prom.Counter("modmail_discord_events", "The total number of processed events.", ["type"])
dispatch_counter = prom.Counter("modmail_dispatch_events", "The total number of dispatched events.", ["type"])

guilds_join_counter = prom.Counter("modmail_guilds_join", "The number of guilds ModMail is added to.")
guilds_leave_counter = prom.Counter("modmail_guilds_leave", "The number of guilds ModMail is removed from.")

shards_counter = prom.Gauge("modmail_shards", "The total number of shards on this cluster.")
guilds_counter = prom.Gauge("modmail_guilds", "The total number of guilds on this cluster.")
users_counter = prom.Gauge("modmail_users", "The total number of users on this cluster.")

commands_counter = prom.Counter("modmail_commands", "The total number of commands used on the bot.", ["name"])
tickets_counter = prom.Counter("modmail_tickets", "The total number of tickets created by the bot.")
tickets_message_counter = prom.Counter("modmail_tickets_message", "The total number of messages sent through tickets.")


def start(bot):
    port = 6000 + bot.cluster
    prom.start_http_server(port)
    bot.loop.create_task(update_stats(bot))
    bot.loop.create_task(update_latency(bot))


async def update_stats(bot):
    while True:
        await bot.wait_until_ready()
        shards_counter.set(len(bot.shards))
        guilds_counter.set(len(bot.guilds))
        users_counter.set(len(bot.users))
        await asyncio.sleep(30)


async def update_latency(bot):
    while True:
        if not bot.is_ready():
            await bot.wait_until_ready()
            await asyncio.sleep(30)
        latency_counter.set(bot.latency)
        await asyncio.sleep(10)

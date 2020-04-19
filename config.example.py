# Bot's token
token = ""

# DiscordBotList token
dbl_token = ""

# Discord Bots token
dbots_token = ""

# Bots on Discord token
bod_token = ""

# Bots for Discord token
bfd_token = ""

# Discord Boats token
dboats_token = ""

# Sentry URL
sentry_url = ""

# Whether the bot is for testing, if true, stats and errors will not be posted
testing = True

# PUBSUB channel for Redis
ipc_channel = ""

# Postgres database credentials
database = {"database": "", "user": "", "password": "", "host": "", "port": 5432}

# Number of shards for each cluster
shards_per_cluster = 4

# Additional shards to launch
additional_shards = 0

# The default prefix for commands
default_prefix = "="

# Status of the bot
activity = [
    f"DM to Contact Staff | {default_prefix}help",
]

# The main bot owner
owner = 000000000000000000

# Bot owners that have access to owner commands
owners = []

# Bot admins that have access to admin commands
admins = []

# Cogs to load on startup
initial_extensions = [
    "cogs.admin",
    "cogx.communication",
    "cogs.configuration",
    "cogs.core",
    "cogs.direct_message",
    "cogs.error_handler",
    "cogs.events",
    "cogs.general",
    "cogs.miscellaneous",
    "cogs.modmail_channel",
    "cogs.owner",
    "cogs.premium",
    "cogs.snippet",
]

# Channels to send logs
join_channel = 000000000000000000
event_channel = 000000000000000000
admin_channel = 000000000000000000

# This is where patron roles are at
main_server = 000000000000000000

# Patron roles for premium servers
premium1 = 000000000000000000
premium3 = 000000000000000000
premium5 = 000000000000000000

# The colour used in embeds
primary_colour = 0x1E90FF
user_colour = 0x00FF00
mod_colour = 0xFF4500
error_colour = 0xFF0000

# Version of bot
__version__ = "1.4.0"

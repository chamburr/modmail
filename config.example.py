# Bot's token
token = ""

# Top.gg token
topgg_token = ""

# Discord Bots token
dbots_token = ""

# Discord Bot List token
dbl_token = ""

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

# AMQP credentials
amqp_url = ""

# Redis credentials
redis_url = ""

# Postgres credentials
postgres_url = ""

# Number of clusters
clusters = 1

# The default prefix for commands
default_prefix = "="

# The server to send tickets to, no confirmation messages if set
default_server = None

# Bot owners that have access to owner commands
owners = []

# Bot admins that have access to admin commands
admins = []

# Cogs to load on startup
cogs = [
    "configuration",
    "core",
    "events",
    "error_handler",
    "owner",
    "general",
]

# Channels to send logs
admin_channel = None

# This is where patron roles are at
main_server = None

# Patron roles for premium servers
premium1 = None
premium3 = None
premium5 = None

# The colour used in embeds
primary_colour = 0x1E90FF
user_colour = 0x00FF00
mod_colour = 0xFF4500
error_colour = 0xFF0000

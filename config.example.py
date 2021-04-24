# Bot token
token = ""

# Bot list tokens
topgg_token = ""
dbots_token = ""
dbl_token = ""
bod_token = ""
bfd_token = ""
dboats_token = ""

# Sentry URL
sentry_url = ""

# Number of clusters
clusters = 1

# Whether the bot is for testing, if true, stats and errors will not be posted
testing = False

# Postgres credentials
database = {
    "database": "modmail",
    "user": "postgres",
    "password": "",
    "host": "127.0.0.1",
    "port": 5432,
}

# Redis credentials
redis = {
    "host": "127.0.0.1",
    "port": 6379,
    "password": None,
}

# RabbitMQ credentials
rabbitmq = {
    "username": "guest",
    "password": "guest",
    "host": "127.0.0.1",
    "port": 5672,
}

# HTTP API Server
http_api = {
    "host": "127.0.0.1",
    "port": 6000,
}

# Default prefix for commands
default_prefix = "="

# Server to send tickets to, no confirmation messages if set
default_server = None

# Bot owners
owners = []

# Bot admins
admins = []

# Admin logs channel
admin_channel = None

# Premium server and roles
main_server = None
premium1 = None
premium3 = None
premium5 = None

# Embed colours
primary_colour = 0x1E90FF
user_colour = 0x00FF00
mod_colour = 0xFF4500
error_colour = 0xFF0000

# Bot's token
token = "NTc1MjUyNjY5NDQzMjExMjY0.XNFSxw.vMA00KwiHxSOr_rJoFKRq9cv8l4"

# The default prefix for commands
default_prefix = "="

# The very very main bot owner
owner = 446290930723717120

# Bot owners that have access to owner commands
admins = [
    446290930723717120,  # CHamburr#2591
    402753815046127627,  # Akaitsune#3426
    458932042252419072,  # KnightOfTla#2075
    415416051170541588,  # xXMareXx7700
    98822055402688512,   # ZixeSea#1234
]

# Cogs to load on startup
initial_extensions = [
    "cogs.configuration",
    "cogs.direct_message",
    "cogs.error_handler",
    "cogs.events",
    "cogs.general",
    "cogs.main",
    "cogs.miscellaneous",
    "cogs.modmail_channel",
    "cogs.owner",
    "cogs.premium",
]

# Channels to send logs
join_channel = 576954178153480233
event_channel = 576954202308214785
error_channel = 578549440365854730

# The colour used in embeds
primary_colour = 0x1E90FF
user_colour = 0x00FF00
mod_colour = 0xFF4500
error_colour = 0xFF0000

# Version of bot
__version__ = "1.0.0"

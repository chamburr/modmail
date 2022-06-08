import logging
import typing

from discord.errors import Forbidden
from discord.ext import commands
from discord.permissions import PermissionOverwrite
from discord.role import Role

from classes.embed import Embed, ErrorEmbed
from utils import checks, tools
from utils.converters import ChannelConverter, PingRoleConverter, RoleConverter

log = logging.getLogger(__name__)


class Configuration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_overwrites(self, ctx, roles):
        overwrites = {await ctx.guild.default_role(): PermissionOverwrite(read_messages=False)}

        for role in roles:
            role = await ctx.guild.get_role(role)
            if role:
                overwrites[role] = PermissionOverwrite(
                    read_messages=True,
                    read_message_history=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    add_reactions=True,
                )

        return overwrites

    @checks.bot_has_permissions(
        manage_channels=True,
        manage_roles=True,
        read_messages=True,
        read_message_history=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        add_reactions=True,
    )
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(description="Set up ModMail.", usage="setup")
    async def setup(self, ctx):
        msg = await ctx.send(Embed("Setting up..."))

        data = await tools.get_data(self.bot, ctx.guild.id)
        if await ctx.guild.get_channel(data[2]):
            await msg.edit(ErrorEmbed("The bot has already been set up."))
            return

        overwrites = await self._get_overwrites(ctx, data[3])
        category = await ctx.guild.create_category(name="ModMail", overwrites=overwrites)
        logging_channel = await ctx.guild.create_text_channel(name="modmail-log", category=category)

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET category=$1, logging=$2 WHERE guild=$3",
                category.id,
                logging_channel.id,
                ctx.guild.id,
            )

        await msg.edit(
            Embed(
                "Premium",
                "Please consider purchasing premium! It is the best way you can show support to "
                "us. You will get access to premium features including greeting and closing "
                "messages, advanced logging that includes chat history, as well as the snippet "
                "functionality. You will also receive priority support in our server. For more "
                f"information, see `{ctx.prefix}premium`.",
            )
        )

        await ctx.send(
            Embed(
                "Setup",
                "Everything has been set up! Next up, you can give your staff access to ModMail "
                f"commands using `{ctx.prefix}accessrole [roles]` (by default, any user with the "
                f"administrator permission has full access). You can also test things out by "
                f"direct messaging me. Check out more information and configurations with "
                f"`{ctx.prefix}help`.",
            )
        )

    @commands.guild_only()
    @commands.command(
        description="Change the prefix or view the current prefix.",
        usage="prefix [new prefix]",
        aliases=["setprefix"],
    )
    async def prefix(self, ctx, *, prefix: str = None):
        if prefix is None:
            await ctx.send(Embed(f"The prefix for this server is `{ctx.prefix}`."))
            return

        if (await ctx.message.member.guild_permissions()).administrator is False:
            raise commands.MissingPermissions(["administrator"])

        if len(prefix) > 10:
            await ctx.send(ErrorEmbed("The chosen prefix is too long."))
            return

        if prefix == self.bot.config.DEFAULT_PREFIX:
            prefix = None

        await tools.get_data(self.bot, ctx.guild.id)
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE data SET prefix=$1 WHERE guild=$2", prefix, ctx.guild.id)

        await self.bot.state.set(f"prefix:{ctx.guild.id}", "" if prefix is None else prefix)

        await ctx.send(
            Embed(
                "Successfully changed the prefix to "
                f"`{self.bot.config.DEFAULT_PREFIX if prefix is None else prefix}`.",
            )
        )

    @checks.bot_has_permissions(manage_channels=True, manage_roles=True)
    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Re-create the category for the ModMail channels.", usage="category [name]"
    )
    async def category(self, ctx, *, name: str = "ModMail"):
        if len(name) > 100:
            await ctx.send(ErrorEmbed("The category name cannot be longer than 100 characters"))
            return

        data = await tools.get_data(self.bot, ctx.guild.id)
        if await ctx.guild.get_channel(data[2]):
            await ctx.send(
                ErrorEmbed(
                    "A ModMail category already exists. Please delete that category and try again."
                )
            )
            return

        overwrites = await self._get_overwrites(ctx, data[3])
        category = await ctx.guild.create_category(name=name, overwrites=overwrites)

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET category=$1 WHERE guild=$2", category.id, ctx.guild.id
            )

        await ctx.send(Embed("Successfully created the category."))

    @checks.bot_has_permissions(manage_channels=True, manage_roles=True)
    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set or clear the roles that have access to ticket related commands and "
        "replying to tickets.",
        aliases=["modrole", "supportrole"],
        usage="accessrole [roles]",
    )
    async def accessrole(self, ctx, roles: commands.Greedy[RoleConverter] = None, *, check=None):
        if roles is None:
            roles = []

        if check:
            await ctx.send(ErrorEmbed("The role(s) are not found. Please try again."))
            return

        if len(roles) > 10:
            await ctx.send(
                ErrorEmbed(
                    "There can at most be 10 roles. Try using the command again but specify fewer "
                    "roles."
                )
            )
            return

        msg = await ctx.send(Embed("Updating roles..."))

        old_data = await tools.get_data(self.bot, ctx.guild.id)

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET accessrole=$1 WHERE guild=$2",
                [role.id for role in roles],
                ctx.guild.id,
            )

        data = await tools.get_data(self.bot, ctx.guild.id)
        category = await ctx.guild.get_channel(data[2])

        if category and roles:
            try:
                for role in old_data[3]:
                    role = await ctx.guild.get_role(role)

                    if role:
                        await category.set_permissions(target=role, overwrite=None)

                for role, permission in (await self._get_overwrites(ctx, data[3])).items():
                    await category.set_permissions(target=role, overwrite=permission)
            except Forbidden:
                await msg.edit(
                    ErrorEmbed(
                        "The role(s) are updated successfully. The permission overwrites for the "
                        "category failed to be changed. Update my permissions and try again or set "
                        "the overwrites manually."
                    )
                )
                return

        await msg.edit(Embed("The role(s) are updated successfully."))

    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set or clear the roles mentioned when a ticket is opened. You can also use "
        "`everyone` and `here`.",
        aliases=["mentionrole"],
        usage="pingrole [roles]",
    )
    async def pingrole(self, ctx, roles: commands.Greedy[PingRoleConverter] = None):
        if roles is None:
            roles = []

        role_ids = []
        for role in roles:
            if not isinstance(role, Role):
                role = role.lower()
                role = role.replace("@", "", 1)

                if role == "everyone":
                    role_ids.append(ctx.guild.id)
                elif role == "here":
                    role_ids.append(-1)
                else:
                    await ctx.send(ErrorEmbed("The role(s) are not found. Please try again."))
                    return
            else:
                role_ids.append(role.id)

        if len(role_ids) > 10:
            await ctx.send(
                ErrorEmbed(
                    "There can at most be 10 roles. Try using the command again but specify fewer "
                    "roles."
                )
            )
            return

        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE data SET pingrole=$1 WHERE guild=$2", role_ids, ctx.guild.id)

        await ctx.send(Embed("The role(s) are updated successfully."))

    @checks.bot_has_permissions(manage_channels=True)
    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Toggle ticket logging and optionally in an existing channel.",
        aliases=["logs"],
        usage="logging [channel]",
    )
    async def logging(self, ctx, channel: typing.Optional[ChannelConverter]):
        data = await tools.get_data(self.bot, ctx.guild.id)

        if data[4] and channel is None:
            async with self.bot.pool.acquire() as conn:
                await conn.execute("UPDATE data SET logging=$1 WHERE guild=$2", None, ctx.guild.id)

            await ctx.send(Embed("ModMail logging is disabled. You may delete the channel."))
            return

        category = await ctx.guild.get_channel(data[2])
        if category is None:
            await ctx.send(
                ErrorEmbed(
                    f"Your server does not have a ModMail category yet. Use either "
                    f"`{ctx.prefix}setup` or `{ctx.prefix}category` to create the category first."
                )
            )
            return

        if channel is None:
            channel = await ctx.guild.create_text_channel(name="modmail-log", category=category)

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET logging=$1 WHERE guild=$2", channel.id, ctx.guild.id
            )

        await ctx.send(Embed("ModMail logging is enabled."))

    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Toggle whether commands are required to reply to a ticket.",
        aliases=["commandrequired"],
        usage="commandonly",
    )
    async def commandonly(self, ctx):
        data = await tools.get_data(self.bot, ctx.guild.id)

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET commandonly=$1 WHERE guild=$2",
                True if data[11] is False else False,
                ctx.guild.id,
            )

        await ctx.send(
            Embed(f"Command only mode is {'enabled' if data[11] is False else 'disabled'}.")
        )

    @checks.in_database()
    @checks.is_premium()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set or clear the message that is sent when a new ticket is opened. Tags "
        "`{username}`, `{usertag}`, `{userid}` and `{usermention}` can be used.",
        aliases=["welcomemessage", "greetmessage"],
        usage="greetingmessage [text]",
    )
    async def greetingmessage(self, ctx, *, text: str = None):
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE data SET welcome=$1 WHERE guild=$2", text, ctx.guild.id)

        await ctx.send(Embed("The greeting message is set successfully."))

    @checks.in_database()
    @checks.is_premium()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set or clear the message that is sent when a ticket is closed. Tags "
        "`{username}`, `{usertag}`, `{userid}` and `{usermention}` can be used.",
        aliases=["goodbyemessage", "closemessage"],
        usage="closingmessage [text]",
    )
    async def closingmessage(self, ctx, *, text: str = None):
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE data SET goodbye=$1 WHERE guild=$2", text, ctx.guild.id)

        await ctx.send(Embed("The closing message is set successfully."))

    @checks.in_database()
    @checks.is_premium()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Toggle advanced logging which includes messages sent and received.",
        aliases=["advancedlogging", "advancedlogs"],
        usage="loggingplus",
    )
    async def loggingplus(self, ctx):
        data = await tools.get_data(self.bot, ctx.guild.id)

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET loggingplus=$1 WHERE guild=$2",
                True if data[7] is False else False,
                ctx.guild.id,
            )

        await ctx.send(
            Embed(f"Advanced logging is {'enabled' if data[7] is False else 'disabled'}.")
        )

    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(description="Toggle default anonymous messages.", usage="anonymous")
    async def anonymous(self, ctx):
        data = await tools.get_data(self.bot, ctx.guild.id)

        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET anonymous=$1 WHERE guild=$2",
                True if data[10] is False else False,
                ctx.guild.id,
            )

        await ctx.send(
            Embed(f"Anonymous messaging is {'enabled' if data[10] is False else 'disabled'}.")
        )

    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="View the configurations for the current server.", usage="viewconfig"
    )
    async def viewconfig(self, ctx):
        data = await tools.get_data(self.bot, ctx.guild.id)
        category = await ctx.guild.get_channel(data[2])
        logging_channel = await ctx.guild.get_channel(data[4])

        access_roles = []
        for role in data[3]:
            access_roles.append(f"<@&{role}>")

        ping_roles = []
        for role in data[8]:
            if role == -1:
                ping_roles.append("@here")
            elif role == ctx.guild.id:
                ping_roles.append("@everyone")
            else:
                ping_roles.append(f"<@&{role}>")

        greeting = data[5]
        if greeting and len(greeting) > 1000:
            greeting = greeting[:997] + "..."

        closing = data[6]
        if closing and len(closing) > 1000:
            closing = closing[:997] + "..."

        embed = Embed(title="Server Configurations")
        embed.add_field("Prefix", ctx.prefix)
        embed.add_field("Category", "*Not set*" if category is None else category.name)
        embed.add_field(
            "Access Roles",
            "*Not set*" if len(access_roles) == 0 else " ".join(access_roles),
        )
        embed.add_field("Ping Roles", "*Not set*" if len(ping_roles) == 0 else " ".join(ping_roles))
        embed.add_field(
            "Logging",
            "*Not set*" if logging_channel is None else f"<#{logging_channel.id}>",
        )
        embed.add_field("Advanced Logging", "Enabled" if data[7] is True else "Disabled")
        embed.add_field("Anonymous Messaging", "Enabled" if data[10] is True else "Disabled")
        embed.add_field("Command Only Mode", "Enabled" if data[11] is True else "Disabled")
        embed.add_field("Greeting Message", "*Not set*" if greeting is None else greeting, False)
        embed.add_field("Closing Message", "*Not set*" if closing is None else closing, False)

        await ctx.send(embed)


def setup(bot):
    bot.add_cog(Configuration(bot))

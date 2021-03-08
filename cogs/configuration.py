import logging

import discord

from discord.ext import commands

from classes import converters
from classes.converters import RoleConverter
from utils import checks

log = logging.getLogger(__name__)


class Configuration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_permission = discord.PermissionOverwrite(
            read_messages=True,
            read_message_history=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            add_reactions=True,
        )
        self.default_role_permission = discord.PermissionOverwrite(read_messages=False)

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
        category_name = "ModMail"
        msg = await ctx.send(embed=discord.Embed(description="Setting up...", colour=self.bot.primary_colour))
        data = await self.bot.get_data(ctx.guild.id)
        overwrites = {await ctx.guild.default_role(): self.default_role_permission}
        for role in [await ctx.guild.get_role(role) for role in data[3]]:
            if role is None:
                continue
            overwrites[role] = self.role_permission
        category = await ctx.guild.create_category_channel(name=category_name, overwrites=overwrites)
        logging_channel = await ctx.guild.create_text_channel(name="modmail-log", category=category)
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET category=$1, logging=$2 WHERE guild=$3",
                category.id,
                logging_channel.id,
                ctx.guild.id,
            )
        await msg.edit(
            embed=discord.Embed(
                title="Premium",
                description="Please consider purchasing premium! It is the best way you can show support to us. You "
                "will get access to premium features including greeting and closing messages, advanced logging that "
                "includes chat history, as well as the snippet functionality. You will also receive priority support "
                f"in our server. For more information, see `{ctx.prefix}premium`.",
                colour=self.bot.primary_colour,
            )
        )
        await ctx.send(
            embed=discord.Embed(
                title="Setup",
                description="Everything has been set up! Next up, you can give your staff access to ModMail commands "
                f"using `{ctx.prefix}accessrole [roles]` (by default, any user with the administrator permission has "
                "full access). You can also test things out by direct messaging me. Check out more information and "
                f"configurations with `{ctx.prefix}help`.",
                colour=self.bot.primary_colour,
            )
        )

    @commands.guild_only()
    @commands.command(
        description="Change the prefix or view the current prefix.", usage="prefix [new prefix]", aliases=["setprefix"]
    )
    async def prefix(self, ctx, *, prefix: str = None):
        if prefix is None:
            await ctx.send(
                embed=discord.Embed(
                    description=f"The prefix for this server is `{ctx.prefix}`.",
                    colour=self.bot.primary_colour,
                )
            )
            return
        if (await ctx.message.member()).guild_permissions.administrator is False:
            raise commands.MissingPermissions(["administrator"])
        else:
            if len(prefix) > 10:
                await ctx.send(
                    embed=discord.Embed(
                        description="The chosen prefix is too long.",
                        colour=self.bot.error_colour,
                    )
                )
                return
            if prefix == self.bot.config.default_prefix:
                prefix = None
            await self.bot.get_data(ctx.guild.id)
            async with self.bot.pool.acquire() as conn:
                await conn.execute("UPDATE data SET prefix=$1 WHERE guild=$2", prefix, ctx.guild.id)
            self.bot.all_prefix[ctx.guild.id] = prefix
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully changed the prefix to "
                    f"`{self.bot.config.default_prefix if prefix is None else prefix}`.",
                    colour=self.bot.primary_colour,
                )
            )

    @checks.bot_has_permissions(manage_channels=True, manage_roles=True)
    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(description="Re-create the category for the ModMail channels.", usage="category [name]")
    async def category(self, ctx, *, name: str = "ModMail"):
        if len(name) > 100:
            await ctx.send(
                embed=discord.Embed(
                    description="The category name cannot be longer than 100 characters",
                    colour=self.bot.error_colour,
                )
            )
            return
        data = await self.bot.get_data(ctx.guild.id)
        if await ctx.guild.get_channel(data[2]):
            await ctx.send(
                embed=discord.Embed(
                    description="A ModMail category already exists. Please delete that category and try again.",
                    colour=self.bot.error_colour,
                )
            )
            return
        overwrites = {await ctx.guild.default_role(): self.default_role_permission}
        for role in [await ctx.guild.get_role(role) for role in data[3]]:
            if role is None:
                continue
            overwrites[role] = self.role_permission
        category = await ctx.guild.create_category_channel(name=name, overwrites=overwrites)
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE data SET category=$1 WHERE guild=$2", category.id, ctx.guild.id)
        await ctx.send(
            embed=discord.Embed(description="Successfully created the category.", colour=self.bot.primary_colour)
        )

    @checks.bot_has_permissions(manage_channels=True, manage_roles=True)
    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set or clear the roles that have access to ticket related commands and replying to tickets.",
        aliases=["modrole", "supportrole"],
        usage="accessrole [roles]",
    )
    async def accessrole(self, ctx, roles: commands.Greedy[RoleConverter] = None, *, check=None):
        if roles is None:
            roles = []
        if check:
            await ctx.send(
                embed=discord.Embed(
                    description="The role(s) are not found. Please try again.",
                    colour=self.bot.error_colour,
                )
            )
            return
        if len(roles) > 10:
            await ctx.send(
                embed=discord.Embed(
                    description="There can at most be 10 roles. Try using the command again but specify less roles.",
                    colour=self.bot.error_colour,
                )
            )
            return
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET accessrole=$1 WHERE guild=$2",
                [role.id for role in roles],
                ctx.guild.id,
            )
        category = (await self.bot.get_data(ctx.guild.id))[2]
        category = await ctx.guild.get_channel(category)
        if category and roles:
            try:
                for role in roles:
                    await category.set_permissions(target=role, overwrite=self.role_permission)
                await category.set_permissions(
                    target=(await ctx.guild.default_role()), overwrite=self.default_role_permission
                )
            except discord.Forbidden:
                await ctx.send(
                    embed=discord.Embed(
                        description="The role(s) are updated successfully. The permission overwrites for the category "
                        "failed to be changed. Update my permissions and try again or set the overwrites manually.",
                        colour=self.bot.error_colour,
                    )
                )
                return
        await ctx.send(
            embed=discord.Embed(description="The role(s) are updated successfully.", colour=self.bot.primary_colour)
        )

    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set or clear the roles mentioned when a ticket is opened. You can also use `everyone` and `here`.",
        aliases=["mentionrole"],
        usage="pingrole [roles]",
    )
    async def pingrole(self, ctx, roles: commands.Greedy[converters.RoleConverter] = None):
        if roles is None:
            roles = []
        role_ids = []
        for role in roles:
            if not isinstance(role, discord.Role):
                role = role.lower()
                role = role.replace("@", "", 1)
                if role == "everyone":
                    role_ids.append((await ctx.guild.default_role()).id)
                elif role == "here":
                    role_ids.append(-1)
                else:
                    await ctx.send(
                        embed=discord.Embed(
                            description="The role(s) are not found. Please try again.",
                            colour=self.bot.error_colour,
                        )
                    )
                    return
            else:
                role_ids.append(role.id)
        if len(role_ids) > 10:
            await ctx.send(
                embed=discord.Embed(
                    description="There can at most be 10 roles. Try using the command again but specify less roles.",
                    colour=self.bot.error_colour,
                )
            )
            return
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE data SET pingrole=$1 WHERE guild=$2", role_ids, ctx.guild.id)
        await ctx.send(
            embed=discord.Embed(
                description="The role(s) are updated successfully.",
                colour=self.bot.primary_colour,
            )
        )

    @checks.bot_has_permissions(manage_channels=True)
    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Toggle between enable and disable for ModMail logs.",
        aliases=["logs"],
        usage="logging",
    )
    async def logging(self, ctx):
        data = await self.bot.get_data(ctx.guild.id)
        channel = await ctx.guild.get_channel(data[4])
        if channel:
            try:
                await channel.delete()
            except discord.Forbidden:
                await ctx.send(
                    embed=discord.Embed(
                        description="Missing permissions to delete the channel.",
                        colour=self.bot.error_colour,
                    )
                )
                return
        if data[4]:
            async with self.bot.pool.acquire() as conn:
                await conn.execute("UPDATE data SET logging=$1 WHERE guild=$2", None, ctx.guild.id)
            await ctx.send(
                embed=discord.Embed(description="ModMail logs are disabled.", colour=self.bot.primary_colour)
            )
        else:
            category = await ctx.guild.get_channel(data[2])
            if category is None:
                await ctx.send(
                    embed=discord.Embed(
                        description=f"Your server does not have a ModMail category yet. Use either `{ctx.prefix}setup` "
                        f"or `{ctx.prefix}category` to create the category first.",
                        colour=self.bot.error_colour,
                    )
                )
                return
            channel = await ctx.guild.create_text_channel(name="modmail-log", category=category)
            async with self.bot.pool.acquire() as conn:
                await conn.execute("UPDATE data SET logging=$1 WHERE guild=$2", channel.id, ctx.guild.id)
            await ctx.send(
                embed=discord.Embed(description="The channel is created successfully.", colour=self.bot.primary_colour)
            )

    @checks.in_database()
    @checks.is_premium()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set or clear the message that is sent when a new ticket is opened. Tags `{username}`, "
        "`{usertag}`, `{userid}` and `{usermention}` can be used.",
        aliases=["welcomemessage", "greetmessage"],
        usage="greetingmessage [text]",
    )
    async def greetingmessage(self, ctx, *, text: str = None):
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE data SET welcome=$1 WHERE guild=$2", text, ctx.guild.id)
        await ctx.send(
            embed=discord.Embed(description="The greeting message is set successfully.", colour=self.bot.primary_colour)
        )

    @checks.in_database()
    @checks.is_premium()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set or clear the message that is sent when a ticket is closed. Tags `{username}`, "
        "`{usertag}`, `{userid}` and `{usermention}` can be used.",
        aliases=["goodbyemessage", "closemessage"],
        usage="closingmessage [text]",
    )
    async def closingmessage(self, ctx, *, text: str = None):
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE data SET goodbye=$1 WHERE guild=$2", text, ctx.guild.id)
        await ctx.send(
            embed=discord.Embed(description="The closing message is set successfully.", colour=self.bot.primary_colour)
        )

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
        data = await self.bot.get_data(ctx.guild.id)
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET loggingplus=$1 WHERE guild=$2",
                True if data[7] is False else False,
                ctx.guild.id,
            )
        await ctx.send(
            embed=discord.Embed(
                description=f"Advanced logging is {'enabled' if data[7] is False else 'disabled'}.",
                colour=self.bot.primary_colour,
            )
        )

    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(description="Toggle default anonymous messages.", usage="anonymous")
    async def anonymous(self, ctx):
        data = await self.bot.get_data(ctx.guild.id)
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "UPDATE data SET anonymous=$1 WHERE guild=$2",
                True if data[10] is False else False,
                ctx.guild.id,
            )
        await ctx.send(
            embed=discord.Embed(
                description=f"Anonymous messaging is {'enabled' if data[10] is False else 'disabled'}.",
                colour=self.bot.primary_colour,
            )
        )

    @checks.in_database()
    @checks.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(description="View the configurations for the current server.", usage="viewconfig")
    async def viewconfig(self, ctx):
        data = await self.bot.get_data(ctx.guild.id)
        category = await ctx.guild.get_channel(data[2])
        logging = await ctx.guild.get_channel(data[4])
        access_roles = []
        for role in data[3]:
            access_roles.append(f"<@&{role}>")
        ping_roles = []
        for role in data[8]:
            if role == -1:
                ping_roles.append("@here")
            elif role == (await ctx.guild.default_role()).id:
                ping_roles.append("@everyone")
            else:
                ping_roles.append(f"<@&{role}>")
        welcome = data[5]
        if welcome and len(welcome) > 1000:
            welcome = welcome[:997] + "..."
        goodbye = data[6]
        if goodbye and len(goodbye) > 1000:
            goodbye = goodbye[:997] + "..."
        blacklist = []
        for user in data[9]:
            blacklist.append(f"<@{user}>")
        embed = discord.Embed(title="Server Configurations", colour=self.bot.primary_colour)
        embed.add_field(name="Prefix", value=self.bot.tools.get_guild_prefix(self.bot, ctx.guild))
        embed.add_field(name="Category", value="*Not set*" if category is None else category.name)
        embed.add_field(name="Access Roles", value="*Not set*" if len(access_roles) == 0 else " ".join(access_roles))
        embed.add_field(name="Ping Roles", value="*Not set*" if len(ping_roles) == 0 else " ".join(ping_roles))
        embed.add_field(name="Logging", value="*Not set*" if logging is None else f"<#{logging.id}>")
        embed.add_field(name="Advanced Logging", value="Enabled" if data[7] is True else "Disabled")
        embed.add_field(name="Anonymous Messaging", value="Enabled" if data[10] is True else "Disabled")
        embed.add_field(name="Greeting Message", value="*Not set*" if welcome is None else welcome, inline=False)
        embed.add_field(name="Closing message", value="*Not set*" if goodbye is None else goodbye, inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Configuration(bot))

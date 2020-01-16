import asyncio
import discord
from discord.ext import commands

from utils import checks


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

    @commands.bot_has_permissions(
        manage_channels=True,
        manage_roles=True,
        read_messages=True,
        read_message_history=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        add_reactions=True,
    )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set up ModMail with an interactive guide.", usage="setup",
    )
    async def setup(self, ctx):
        def check(msg):
            return msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id

        try:
            await ctx.send(
                embed=discord.Embed(
                    title="Step 1 of 2",
                    description="ModMail will create a channel when a user sends a message to the bot. Please enter a "
                    "name for the category that will contain these channels. You may change this manually afterwards.",
                    colour=self.bot.primary_colour,
                )
            )
            category_name = await self.bot.wait_for("message", timeout=60, check=check)
            category_name = category_name.content
            if len(category_name) > 100:
                return await ctx.send(
                    embed=discord.Embed(
                        description="The name of the category cannot be longer than 100 characters."
                        f"Please use `{ctx.prefix}setup` to try again.",
                        colour=self.bot.error_colour,
                    )
                )
            await ctx.send(
                embed=discord.Embed(
                    title="Step 2 of 2",
                    description="Do you want a channel for ModMail logs? It will log the details whenever a "
                    "ticket is created or closed. Please enter either `yes` or `no`. You can change the "
                    "name of this channel manually afterwards.",
                    colour=self.bot.primary_colour,
                )
            )
            modmail_log = await self.bot.wait_for("message", timeout=60, check=check)
            if modmail_log.content.lower() == "yes":
                modmail_log = True
            elif modmail_log.content.lower() == "no":
                modmail_log = False
            else:
                return await ctx.send(
                    embed=discord.Embed(
                        description=f"Answer with `yes` or `no` only. Please use `{ctx.prefix}setup` to try again.",
                        colour=self.bot.error_colour,
                    )
                )
        except asyncio.TimeoutError:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"Time out. Please use `{ctx.prefix}setup` to try again.", colour=self.bot.error_colour,
                )
            )
        await ctx.send(
            embed=discord.Embed(
                title="Premium",
                description="Please consider purchasing premium! It is the best way you can support us. "
                "You will get access to premium features including custom messages when a ticket is created  "
                "or closed and advanced logs that include messages sent and received. You will also receive "
                f"priority support in our server. For more information, see `{ctx.prefix}premium`.",
                colour=self.bot.primary_colour,
            )
        )
        m = await ctx.send(embed=discord.Embed(description="Setting up...", colour=self.bot.primary_colour))
        data = self.bot.get_data(ctx.guild.id)
        overwrites = {ctx.guild.default_role: self.default_role_permission}
        if data[3]:
            for role in [ctx.guild.get_role(role) for role in data[3].split(",")]:
                if role is None:
                    continue
                overwrites[role] = self.role_permission
        category = await ctx.guild.create_category_channel(name=category_name, overwrites=overwrites)
        logging_channel = None
        if modmail_log is True:
            logging_channel = await ctx.guild.create_text_channel(name="modmail-log", category=category)
        if data[2] and data[2] in self.bot.all_category:
            self.bot.all_category.remove(data[2])
        self.bot.all_category.append(category.id)
        c = self.bot.conn.cursor()
        c.execute(
            "UPDATE data SET category=?, logging=? WHERE guild=?",
            (category.id, logging_channel.id if logging_channel else None, ctx.guild.id,),
        )
        self.bot.conn.commit()
        await m.edit(
            embed=discord.Embed(
                description="Everything has been set up! Next up, you can give your staff access to ModMail commands"
                f"using `{ctx.prefix}accessrole [roles]` (by default, any user with the administrator permission has "
                "full access). You can also test things out by direct messaging me. Check out more information and "
                f"configurations with `{ctx.prefix}help`.",
                colour=self.bot.primary_colour,
            )
        )

    @commands.guild_only()
    @commands.command(
        description="Change the prefix or view the current prefix.", usage="prefix [new prefix]", aliases=["setprefix"],
    )
    async def prefix(self, ctx, *, prefix: str = None):
        if prefix is None:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"The prefix for this server is `{ctx.prefix}`.", colour=self.bot.primary_colour,
                )
            )
        if ctx.author.guild_permissions.administrator is False:
            raise commands.MissingPermissions(["administrator"])
        else:
            if len(prefix) > 10:
                return await ctx.send(
                    embed=discord.Embed(description="The chosen prefix is too long.", colour=self.bot.error_colour,)
                )
            if prefix == self.bot.config.default_prefix:
                prefix = None
            self.bot.get_data(ctx.guild.id)
            c = self.bot.conn.cursor()
            c.execute("UPDATE data SET prefix=? WHERE guild=?", (prefix, ctx.guild.id))
            self.bot.conn.commit()
            self.bot.all_prefix[ctx.guild.id] = prefix
            await ctx.send(
                embed=discord.Embed(
                    description="Successfully changed the prefix to "
                    f"`{self.bot.config.default_prefix if prefix is None else prefix}`.",
                    colour=self.bot.primary_colour,
                )
            )

    @commands.bot_has_permissions(manage_channels=True, manage_roles=True)
    @checks.in_database()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Re-create the category for the ModMail channels.", usage="category [name]",
    )
    async def category(self, ctx, *, name: str = "ModMail"):
        if len(name) > 100:
            return await ctx.send(
                embed=discord.Embed(
                    description="The category name cannot be longer than 100 characters", colour=self.bot.error_colour,
                )
            )
        data = self.bot.get_data(ctx.guild.id)
        if ctx.guild.get_channel(data[2]):
            return await ctx.send(
                embed=discord.Embed(
                    description=f"A ModMail category already exists. Please delete that category and try again.",
                    colour=self.bot.error_colour,
                )
            )
        overwrites = {ctx.guild.default_role: self.default_role_permission}
        if data[3]:
            for role in [ctx.guild.get_role(role) for role in data[3].split(",")]:
                if role is None:
                    continue
                overwrites[role] = self.role_permission
        category = await ctx.guild.create_category_channel(name=name, overwrites=overwrites)
        if data[2] and data[2] in self.bot.all_category:
            self.bot.all_category.remove(data[2])
        self.bot.all_category.append(category.id)
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET category=? WHERE guild=?", (category.id, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(description="Successfully created the category.", colour=self.bot.primary_colour,)
        )

    @commands.bot_has_permissions(manage_channels=True, manage_roles=True)
    @checks.in_database()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set or clear the roles that have access to ticket related commands and replying to tickets.",
        aliases=["modrole", "supportrole"],
        usage="accessrole [roles]",
    )
    async def accessrole(self, ctx, roles: commands.Greedy[discord.Role] = None):
        if roles and len(roles) > 10:
            return await ctx.send(
                embed=discord.Embed(
                    description="There can at most be 10 roles. Try using the command again but specify less roles.",
                    colour=self.bot.error_colour,
                )
            )
        c = self.bot.conn.cursor()
        c.execute(
            "UPDATE data SET accessrole=? WHERE guild=?",
            (None if roles is None else ",".join([str(role.id) for role in roles]), ctx.guild.id),
        )
        self.bot.conn.commit()
        category = self.bot.get_data(ctx.guild.id)[2]
        category = ctx.guild.get_channel(category)
        if category and roles:
            try:
                for role in roles:
                    await category.set_permissions(target=role, overwrite=self.role_permission)
                await category.set_permissions(target=ctx.guild.default_role, overwrite=self.default_role_permission)
            except discord.Forbidden:
                return await ctx.send(
                    embed=discord.Embed(
                        description="The role(s) are updated successfully. The permission overwrites for the category "
                        "failed to be changed. Update my permissions and try again or set the overwrites manually.",
                        colour=self.bot.error_colour,
                    )
                )
        await ctx.send(
            embed=discord.Embed(description="The role(s) are updated successfully.", colour=self.bot.primary_colour,)
        )

    @checks.in_database()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set or clear the role mentioned when a ticket is opened. You can also use `everyone` and `here`.",
        aliases=["mentionrole"],
        usage="pingrole [role]",
    )
    async def pingrole(self, ctx, *, role=None):
        c = self.bot.conn.cursor()
        if role:
            if role.lower().replace("@", "") in ["here", "everyone"]:
                role = f"@{role.lower()}"
            else:
                role = await commands.RoleConverter().convert(ctx, role)
                if role is None:
                    return await ctx.send(
                        embed=discord.Embed(
                            description="The role is not found. Please try again.", colour=self.bot.error_colour,
                        )
                    )
                else:
                    role = role.id
        c.execute("UPDATE data SET pingrole=? WHERE guild=?", (role, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(
                description=f"The role mentioned is updated successfully.", colour=self.bot.primary_colour,
            )
        )

    @commands.bot_has_permissions(manage_channels=True)
    @checks.in_database()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Toggle between enable and disable for ModMail logs.",
        aliases=["logging", "modmaillogs"],
        usage="logs",
    )
    async def logs(self, ctx):
        data = self.bot.get_data(ctx.guild.id)
        channel = ctx.guild.get_channel(data[4])
        if channel:
            try:
                await channel.delete()
            except discord.Forbidden:
                return await ctx.send(
                    embed=discord.Embed(
                        description="Missing permissions to delete the channel.", colour=self.bot.error_colour,
                    )
                )
        if data[4]:
            c = self.bot.conn.cursor()
            c.execute("UPDATE data SET logging=? WHERE guild=?", (None, ctx.guild.id))
            self.bot.conn.commit()
            await ctx.send(
                embed=discord.Embed(description="ModMail logs are disabled.", colour=self.bot.primary_colour,)
            )
        else:
            category = ctx.guild.get_channel(data[2])
            if category is None:
                return await ctx.send(
                    embed=discord.Embed(
                        description=f"Your server does not have a ModMail category yet. Use either `{ctx.prefix}setup` "
                        f"or `{ctx.prefix}category` to create the category first.",
                        colour=self.bot.error_colour,
                    )
                )
            channel = await ctx.guild.create_text_channel(name="modmail-log", category=category)
            c = self.bot.conn.cursor()
            c.execute("UPDATE data SET logging=? WHERE guild=?", (channel.id, ctx.guild.id))
            self.bot.conn.commit()
            await ctx.send(
                embed=discord.Embed(description="The channel is created successfully.", colour=self.bot.primary_colour,)
            )

    @checks.in_database()
    @checks.is_premium()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set or clear the message that is sent when a new ticket is opened.",
        usage="greetingmessage [text]",
    )
    async def greetingmessage(self, ctx, *, text=None):
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET welcome=? WHERE guild=?", (text, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(
                description="The greeting message is set successfully.", colour=self.bot.primary_colour,
            )
        )

    @checks.in_database()
    @checks.is_premium()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set or clear the message that is sent when a ticket is closed.", usage="closemessage [text]",
    )
    async def closemessage(self, ctx, *, text=None):
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET goodbye=? WHERE guild=?", (text, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(description="The close message is set successfully.", colour=self.bot.primary_colour,)
        )

    @checks.in_database()
    @checks.is_premium()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Toggle advanced logging which includes all messages.", usage="loggingplus",
    )
    async def loggingplus(self, ctx):
        data = self.bot.get_data(ctx.guild.id)
        c = self.bot.conn.cursor()
        if data[7] is None:
            c.execute("UPDATE data SET loggingplus=? WHERE guild=?", (1, ctx.guild.id))
            await ctx.send(
                embed=discord.Embed(description="Advanced logging is enabled.", colour=self.bot.primary_colour,)
            )
        else:
            c.execute("UPDATE data SET loggingplus=? WHERE guild=?", (None, ctx.guild.id))
            await ctx.send(
                embed=discord.Embed(description="Advanced logging is disabled.", colour=self.bot.primary_colour,)
            )
        self.bot.conn.commit()


def setup(bot):
    bot.add_cog(Configuration(bot))

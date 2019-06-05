import asyncio
import discord
from discord.ext import commands

from utils import checks


class Configuration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        description="Set me up and immerse your server into this amazing ModMail.",
        usage="setup",
    )
    async def setup(self, ctx):
        def check(msg):
            return msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id
        try:
            await ctx.send(
                embed=discord.Embed(
                    title="Step 1 of 4",
                    description="ModMail will create a channel when a user sends a message to the bot. Please enter a "
                                "name for the category that will contain these channels. You may change this "
                                "manually afterwards.",
                    color=self.bot.primary_colour,
                )
            )
            category_name = await self.bot.wait_for("message", timeout=60, check=check)
            category_name = category_name.content
            if len(category_name) > 100:
                return await ctx.send(
                    embed=discord.Embed(
                        description="The name of the category cannot be longer than 100 characters."
                                    f"Please use `{ctx.prefix}setup` to try again.",
                        color=self.bot.primary_colour,
                    )
                )
            await ctx.send(
                embed=discord.Embed(
                    title="Step 2 of 4",
                    description="Please input a role which has access to the ModMail channels and commands. They will "
                                "be able to reply to the users and close the tickets. You can either enter the role "
                                "ID, mention the role, or enter the name of a role.",
                    color=self.bot.primary_colour,
                )
            )
            access_role = await self.bot.wait_for("message", timeout=60, check=check)
            access_role = await commands.RoleConverter().convert(ctx, access_role.content)
            if not access_role:
                return await ctx.send(
                    embed=discord.Embed(
                        description=f"The provided role is invalid. Please use `{ctx.prefix}setup` to try again.",
                        color=self.bot.primary_colour,
                    )
                )
            await ctx.send(
                embed=discord.Embed(
                    title="Step 3 of 4",
                    description="Please input a role to mention when a ticket is opened. The role selected must be set "
                                "to mentionable by everyone. You can either enter the role ID, mention the role, or "
                                "enter the name of a role. You can also enter `here` and `everyone`. If you do not "
                                "want any role to be mentioned, reply with `None`.",
                    color=self.bot.primary_colour,
                )
            )
            ping_role = await self.bot.wait_for("message", timeout=60, check=check)
            if ping_role.content.lower() == "none":
                ping_role = None
            elif ping_role.content.lower() in ["here", "everyone"]:
                ping_role = f"@{ping_role.content.lower()}"
            else:
                ping_role = await commands.RoleConverter().convert(ctx, ping_role.content)
                if not ping_role:
                    return await ctx.send(
                        embed=discord.Embed(
                            description=f"The provided role is invalid. Please use `{ctx.prefix}setup` to try again.",
                            color=self.bot.primary_colour,
                        )
                    )
            await ctx.send(
                embed=discord.Embed(
                    title="Step 4 of 4",
                    description="Do you want a channel for ModMail logs as well? It will log the details whenever a "
                                "ticket is created or closed. Please enter either `yes` or `no`. You can change the "
                                "name of this channel manually afterwards.",
                    color=self.bot.primary_colour,
                )
            )
            modmail_log = await self.bot.wait_for("message", timeout=60, check=check)
            if modmail_log.content.lower() in ["yes", "y"]:
                modmail_log = True
            elif modmail_log.content.lower() in ["no", "n"]:
                modmail_log = False
            else:
                modmail_log = None
            if modmail_log is None:
                return await ctx.send(
                    embed=discord.Embed(
                        description=f"Answer with `yes` or `no` only. Please use `{ctx.prefix}setup` to try again.",
                        color=self.bot.primary_colour,
                    )
                )
        except asyncio.TimeoutError:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"Time out. Please use `{ctx.prefix}setup` to try again.",
                    color=self.bot.primary_colour,
                )
            )
        await ctx.send(
            embed=discord.Embed(
                title="Premium",
                description="Please consider buying premium! It is the best way that you can show support to us. "
                            "You will also get access to premium features such as custom messages to the user when "
                            "a ticket is created and closed, advanced logs that includes all the messages sent and "
                            "received, as well as priority support in our support server.\n\nFor more information "
                            f"on premium, see `{ctx.prefix}premium` or join our support server.",
                color=self.bot.primary_colour,
            )
        )
        m = await ctx.send(
            embed=discord.Embed(
                description="Setting up...",
                color=self.bot.primary_colour,
            )
        )
        overwrites = {
            access_role: discord.PermissionOverwrite(
                read_messages=True,
                read_message_history=True,
                send_messages=True,
                embed_links=True,
                attach_files=True,
                add_reactions=True,
            ),
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        category = await ctx.guild.create_category_channel(name=category_name, overwrites=overwrites)
        logging_channel = None
        if modmail_log is True:
            logging_channel = await ctx.guild.create_text_channel(name="modmail-log", category=category)
        data = self.bot.get_data(ctx.guild.id)
        if data[2] is not None and data[2] in self.bot.all_category:
            self.bot.all_category.remove(data[2])
        self.bot.all_category.append(category.id)
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET category=?, accessrole=?, logging=?, pingrole=? WHERE guild=?", (
            category.id,
            access_role.id,
            logging_channel.id if logging_channel is not None else None,
            str(ping_role.id) if ping_role is not None and ping_role not in ["@here", "@everyone"] else ping_role,
            ctx.guild.id,
        ))
        self.bot.conn.commit()
        await m.edit(
            embed=discord.Embed(
                description="Everything has been set up!",
                color=self.bot.primary_colour,
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
            return await ctx.send(
                embed=discord.Embed(
                    description=f"The prefix for this server is `{ctx.prefix}`.",
                    color=self.bot.primary_colour,
                )
            )
        if ctx.author.guild_permissions.administrator is False:
            raise commands.MissingPermissions(["administrator"])
        else:
            if len(prefix) > 10:
                return await ctx.send(
                    embed=discord.Embed(
                        description="The chosen prefix is too long.",
                        color=self.bot.primary_colour,
                    )
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
                    color=self.bot.primary_colour,
                )
            )

    @commands.bot_has_permissions(
        manage_channels=True,
        manage_roles=True,
    )
    @checks.in_database()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Re-create the category for the ModMail channels.",
        usage="category [name]",
    )
    async def category(self, ctx, *, name: str = "ModMail"):
        if len(name) > 100:
            return await ctx.send(
                embed=discord.Embed(
                    description="The category name cannot be longer than 100 characters",
                    color=self.bot.error_colour,
                )
            )
        data = self.bot.get_data(ctx.guild.id)
        if ctx.guild.get_channel(data[2]) is not None:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"A ModMail category already exists. Please delete that category to continue.",
                    color=self.bot.error_colour,
                )
            )
        role = ctx.guild.get_role(data[3])
        if role is None:
            return await ctx.send(
                embed=discord.Embed(
                    description=f"A valid access role for this server is not set up. Use `{ctx.prefix}accessrole` "
                                "to set the role first.",
                    color=self.bot.error_colour,
                )
            )
        overwrites = {
            role: discord.PermissionOverwrite(
                read_messages=True,
                read_message_history=True,
                send_messages=True,
                embed_links=True,
                attach_files=True,
                add_reactions=True,
            ),
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        category = await ctx.guild.create_category_channel(name=name, overwrites=overwrites)
        if data[2] is not None and data[2] in self.bot.all_category:
            self.bot.all_category.remove(data[2])
        self.bot.all_category.append(category.id)
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET category=? WHERE guild=?", (category.id, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(
                description="Successfully created the category.",
                color=self.bot.primary_colour,
            )
        )

    @checks.in_database()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Update the role that has access to replying and closing tickets.",
        aliases=["modrole", "supportrole"],
        usage="accessrole <role>",
    )
    async def accessrole(self, ctx, *, role: discord.Role):
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET accessrole=? WHERE guild=?", (role.id, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(
                description=f"The role has been updated successfully to <@&{role.id}>",
                color=self.bot.primary_colour,
            )
        )

    @checks.in_database()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Update the role that will be mentioned when a ticket is opened.",
        aliases=["mentionrole"],
        usage="pingrole <role>",
    )
    async def pingrole(self, ctx, *, role):
        c = self.bot.conn.cursor()
        if role.lower() == "none":
            role = None
        elif role.lower() in ["here", "everyone"]:
            role = f"@{role.lower()}"
        else:
            role = await commands.RoleConverter().convert(ctx, role)
            if role is None:
                return await ctx.send(
                    embed=discord.Embed(
                        description="The role is not found. Please try again.",
                        color=self.bot.error_colour,
                    )
                )
            else:
                role = role.id
        c.execute("UPDATE data SET pingrole=? WHERE guild=?", (role, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(
                description=f"The role has been updated successfully.",
                color=self.bot.primary_colour,
            )
        )

    @commands.bot_has_permissions(
        manage_channels=True,
    )
    @checks.in_database()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Toggle between enable and disable for ModMail logs.",
        aliases=["logging", "modmaillogs"],
        usage="logging",
    )
    async def logs(self, ctx):
        data = self.bot.get_data(ctx.guild.id)
        channel = ctx.guild.get_channel(data[4])
        if channel is not None:
            try:
                await channel.delete()
            except discord.Forbidden:
                return await ctx.send(
                    embed=discord.Embed(
                        description="Missing permissions to delete the channel.",
                        color=self.bot.error_colour,
                    )
                )
        if data[4] is not None:
            c = self.bot.conn.cursor()
            c.execute("UPDATE data SET logging=? WHERE guild=?", (None, ctx.guild.id))
            self.bot.conn.commit()
            await ctx.send(
                embed=discord.Embed(
                    description="ModMail logs are disabled.",
                    color=self.bot.primary_colour,
                )
            )
        else:
            category = ctx.guild.get_channel(data[2])
            if category is None:
                return await ctx.send(
                    embed=discord.Embed(
                        description=f"Your server does not have a ModMail category yet. Use either `{ctx.prefix}setup` "
                        f"or `{ctx.prefix}category` to create the category first.",
                        color=self.bot.error_colour,
                    )
                )
            channel = await ctx.guild.create_text_channel(name="modmail-log", category=category)
            c = self.bot.conn.cursor()
            c.execute("UPDATE data SET logging=? WHERE guild=?", (channel.id, ctx.guild.id))
            self.bot.conn.commit()
            await ctx.send(
                embed=discord.Embed(
                    description="The channel has been created successfully.",
                    color=self.bot.primary_colour,
                )
            )

    @checks.in_database()
    @checks.is_premium()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set a super cool greeting message that is sent when a new ticket is opened.",
        usage="greetingmessage [text]",
    )
    async def greetingmessage(self, ctx, *, text=None):
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET welcome=? WHERE guild=?", (text, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(
                description="The greeting message is set successfully",
                color=self.bot.primary_colour,
            )
        )

    @checks.in_database()
    @checks.is_premium()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Set a super cool close message that is sent when a ticket is closed.",
        usage="closemessage [text]",
    )
    async def closemessage(self, ctx, *, text=None):
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET goodbye=? WHERE guild=?", (text, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(
                description="The close message is set successfully",
                color=self.bot.primary_colour,
            )
        )

    @checks.in_database()
    @checks.is_premium()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.command(
        description="Toggle advanced logging which includes all messages.",
        usage="loggingplus",
    )
    async def loggingplus(self, ctx):
        data = self.bot.get_data(ctx.guild.id)
        c = self.bot.conn.cursor()
        if data[7] is None:
            c.execute("UPDATE data SET loggingplus=? WHERE guild=?", (1, ctx.guild.id))
            await ctx.send(
                embed=discord.Embed(
                    description="Advanced logging is enabled.",
                    color=self.bot.primary_colour,
                )
            )
        else:
            c.execute("UPDATE data SET loggingplus=? WHERE guild=?", (None, ctx.guild.id))
            await ctx.send(
                embed=discord.Embed(
                    description="Advanced logging is disabled.",
                    color=self.bot.primary_colour,
                )
            )
        self.bot.conn.commit()


def setup(bot):
    bot.add_cog(Configuration(bot))

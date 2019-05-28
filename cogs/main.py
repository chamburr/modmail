import io
import copy
import datetime
import discord
from discord.ext import commands

from utils import checks
from cogs.modmail_channel import ModMailEvents


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def close_channel(self, ctx, reason, anon: bool = False):
        try:
            await ctx.send(
                embed=discord.Embed(
                    description="Closing channel...",
                    color=self.bot.primary_colour,
                )
            )
            data = self.bot.get_data(ctx.guild.id)
            if data[7] == 1:
                messages = await ctx.channel.history(limit=10000).flatten()
            await ctx.channel.delete()
            embed = discord.Embed(
                title="Ticket Closed",
                description=(reason if reason is not None else "No reason was provided."),
                color=self.bot.error_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_author(
                name=f"{ctx.author.name}#{ctx.author.discriminator}" if anon is False else "Anonymous#0000",
                icon_url=ctx.author.avatar_url if anon is False else
                "https://cdn.discordapp.com/embed/avatars/0.png",
            )
            embed.set_footer(text=f"{ctx.guild.name} | {ctx.guild.id}", icon_url=ctx.guild.icon_url)
            member = ctx.guild.get_member(int(ctx.channel.name))
            if member:
                try:
                    data = self.bot.get_data(ctx.guild.id)
                    if data[6] is not None:
                        embed2 = discord.Embed(
                            title="Custom Close Message",
                            description=data[6],
                            color=self.bot.mod_colour,
                            timestamp=datetime.datetime.utcnow(),
                        )
                        embed2.set_footer(text=f"{ctx.guild.name} | {ctx.guild.id}", icon_url=ctx.guild.icon_url)
                        await member.send(embed=embed2)
                    await member.send(embed=embed)
                except discord.Forbidden:
                    pass
            if data[4] is not None:
                channel = ctx.guild.get_channel(data[4])
                if channel is not None:
                    try:
                        embed.set_footer(
                            text=f"{member.name}#{member.discriminator} | {member.id}",
                            icon_url=member.avatar_url
                        )
                        if data[7] == 1:
                            history = ""
                            for m in messages:
                                if m.author.id != self.bot.user.id or len(m.embeds) <= 0 \
                                   or m.embeds[0].title not in ["Message Received", "Message Sent"]:
                                    continue
                                if not m.embeds[0].author.name:
                                    author = f"{' '.join(m.embeds[0].footer.text.split()[:-2])} (User)"
                                else:
                                    author = f"{m.embeds[0].author.name} (Staff)"
                                description = m.embeds[0].description
                                if len(m.attachments) != 0:
                                    if not description:
                                        description = f"({len(m.attachments)} attachment(s) not shown)"
                                    else:
                                        description = description + f" ({len(m.attachments)} attachment(s) not shown)"
                                history = f"[{str(m.created_at.replace(microsecond=0))}] {author}: " \
                                          f"{description}\n" + history
                            history = io.BytesIO(history.encode())
                            file = discord.File(history, f"modmail_logs_{ctx.channel.name}.txt")
                            return await channel.send(embed=embed, file=file)
                        await channel.send(embed=embed)
                    except discord.Forbidden:
                        pass
        except discord.Forbidden:
            await ctx.send(
                embed=discord.Embed(
                    description="Missing permissions to delete this channel.",
                    color=self.bot.error_colour,
                )
            )

    @checks.is_modmail_channel()
    @checks.is_mod()
    @checks.in_database()
    @commands.guild_only()
    @commands.command(
        description="Anonymously reply to the message.",
        usage="areply <message>",
        aliases=["anonreply"],
    )
    async def areply(self, ctx, *, message):
        modmail = ModMailEvents(self.bot)
        await modmail.send_mail_mod(ctx.message, ctx.prefix, True, message)

    @checks.is_modmail_channel()
    @checks.is_mod()
    @checks.in_database()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(
        description="Close the channel.",
        usage="close [reason]",
        aliases=["end"],
    )
    async def close(self, ctx, *, reason: str = None):
        await self.close_channel(ctx, reason)

    @checks.is_modmail_channel()
    @checks.is_mod()
    @checks.in_database()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(
        description="Anonymously close the channel.",
        usage="aclose [reason]",
        aliases=["anonclose", "aend", "anonend"],
    )
    async def aclose(self, ctx, *, reason: str = None):
        await self.close_channel(ctx, reason, True)


def setup(bot):
    bot.add_cog(Main(bot))

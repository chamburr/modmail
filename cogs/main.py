import io
import datetime
import discord
from discord.ext import commands

from utils import checks


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_modmail_channel()
    @checks.is_mod()
    @checks.in_database()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(
        description="Close the channel.",
        usage="close [reason]",
        aliases=["end", "delete"],
    )
    async def close(self, ctx, *, reason: str = None):
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
                name=f"{ctx.author.name}#{ctx.author.discriminator}",
                icon_url=ctx.author.avatar_url,
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
                                if isinstance(m.embeds[0].author, discord.Embed.Empty):
                                    author = f"{' '.join(m.embeds[0].footer.text.split()[:-2])} (User)"
                                else:
                                    author = f"{m.embeds[0].author.name} (Staff)"
                                description = m.embeds[0].description
                                if len(m.attachments) != 0:
                                    if isinstance(description, discord.Embed.Empty):
                                        description = f"({len(m.attachments)} attachments not shown)"
                                    else:
                                        description = description + f"({len(m.attachments)} attachments not shown)"
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

    @checks.is_mod()
    @checks.in_database()
    @commands.guild_only()
    @commands.command(
        description="Open a ticket with a user.",
        usage="open <user>",
        aliases=["new"],
    )
    async def open(self, ctx, *, user: discord.Member):
        await ctx.send("WIP")


def setup(bot):
    bot.add_cog(Main(bot))

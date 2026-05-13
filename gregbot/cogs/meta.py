from __future__ import annotations

from discord.ext import commands

class MetaCog(commands.Cog):  
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check if greg is alive.")
    async def ping(self, ctx: commands.Context) -> None:
        latency_ms = round(self.bot.latency * 1000)

        await ctx.reply(
            f"Greg is alive. Unfortunately.\n\nLatency: `{latency_ms}ms`",
            mention_author=False,
        )

    @commands.hybrid_command(name="about", description="Learn about Greg.")
    async def about(self, ctx: commands.Context) -> None:
        await ctx.reply(
            (
                "**Greg**\n"
                "A very serious economy bot with a deeply unserious and concerning pickle problem."
            ),
            mention_author=False,
        )
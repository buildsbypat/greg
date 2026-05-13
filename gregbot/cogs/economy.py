from __future__ import annotations

import discord
from discord.ext import commands

from gregbot.config import BotConfig
from gregbot.models.results import CooldownResult, DailyResult, WorkResult
from gregbot.services.economy_service import EconomyService
from gregbot.ui.economy_cards import (
    balance_view,
    cooldown_view,
    daily_view,
    leaderboard_view,
    work_view,
)


class EconomyCog(commands.Cog):
    def __init__(
            self,
            bot: commands.Bot,
            economy: EconomyService,
            config: BotConfig,
    ) -> None:
        self.bot = bot
        self.economy = economy
        self.config = config

    @commands.hybrid_command(
        name="balance",
        aliases=["bal", "wallet"],
        description="Check your pickle stash.",
    )
    async def balance(
        self,
        ctx: commands.Context,
        user: discord.Member | None = None,
    ) -> None:
        if ctx.guild is None:
            await ctx.reply("View your pickles in a server. Not your DM's.", mention_author=False)
            return
        
        target = user or ctx.author

        result = await self.economy.get_balance(
            guild_id=str(ctx.guild.id),
            user_id=str(target.id),
        )

        await ctx.reply(
            view=balance_view(
                user=target,
                result=result,
                config=self.config,
            ),
            mention_author=False,
        )

    @commands.hybrid(name="daily", description="Claim your daily pickles.")
    async def daily(self, ctx: commands.Context) -> None:
        if ctx.guild is None:
            await ctx.reply("Greg only hands out pickles insides servers.", mention_author=False)
            return
        
        result = await self.economy.claim_daily(
            guild_id=str(ctx.guild.id),
            user_id=str(ctx.author.id),
        )

        if isinstance(result, CooldownResult):
            await ctx.reply(
                view=cooldown_view(result, self.config),
                mention_author=False,
            )
            return
        
        if isinstance(result, DailyResult):
            await ctx.reply(
                view=daily_view(ctx.author, result, self.config),
                mention_author=False,
            )
            return
    
    @commands.hybrid_command(name="work", description="Do some deeply questionable work.")
    async def work(self, ctx: commands.Context) -> None:
        if ctx.guild is None:
            await ctx.reply("Greg only recognises work inside servers.", mention_author=False)
            return

        result = await self.economy.work(
            guild_id=str(ctx.guild.id),
            user_id=str(ctx.author.id),
        )

        if isinstance(result, CooldownResult):
            await ctx.reply(
                view=cooldown_view(result, self.config),
                mention_author=False,
            )
            return
        
        if isinstance(result, WorkResult):
            await ctx.reply(
                view=work_view(ctx.author, result, self.config),
                mention_author=False,
            )
            return
    
    @commands.hybrid_command(
        name="leaderboard",
        aliases=["lb", "top"],
        description="show the richest pickle holders.",
    )
    async def leaderboard(self, ctx: commands.Context) -> None:
        if ctx.guild is None:
            await ctx.reply("Greg says a leaderboard with just yourself on it is pretty boring.", mention_author=False)
            return

        rows = await self.economy.get_leaderboard(guild_id=str(ctx.guild.id), limit=10)

        await ctx.reply(
            view=leaderboard_view(rows, self.config),
            mention_author=False,
        )    

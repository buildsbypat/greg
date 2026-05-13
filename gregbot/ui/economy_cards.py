from __future__ import annotations

import discord

from gregbot.config import BotConfig
from gregbot.models.results import BalanceResult, CooldownResult, DailyResult, LeaderboardEntry, WorkResult
from gregbot.ui.components import make_container, separator, simple_view, text_block
from gregbot.ui.copy import PICKLE_FOOTER
from gregbot.ui.theme import COLOR_GREG, COLOR_INFO, COLOR_PICKLE, COLOR_WARNING
from gregbot.utils.money import format_currency
from gregbot.utils.time import format_seconds

def balance_view(
        *,
        user: discord.abc.User,
        result: BalanceResult,
        config: BotConfig,
) -> discord.ui.LayoutView:
    account = result.account

    view = discord.ui.LayoutView(timeout=60)
    view.add_item(
        make_container(
            "🥒 Greg | Balance",
            f"Pickle accounting for {user.mention}.",
            sections=[
                separator(),
                text_block(
                    "**Wallet**\n"
                    f"{format_currency(account.wallet, config=config)}"
                ),
                text_block(
                    "**Bank**\n"
                    f"{format_currency(account.bank, config=config)}"
                ),
                text_block(
                    "**Net Worth**\n"
                    f"{format_currency(account.net_worth, config=config)}"
                ),
                separator(),
                text_block(
                    "**Lifetime earned**\n"
                    f"{format_currency(account.total_earned, config=config)}"
                ),
            ],
            accent_color=COLOR_PICKLE,
            footer="Greg finds this... disturbing.",
        )
    )
    return view

def daily_view(
        user: discord.abc.User,
        result: DailyResult,
        config: BotConfig,
) -> discord.ui.LayoutView:
    view = discord.ui.LayoutView(timeout=60)
    view.add_item(
        make_container(
            "🥒 Greg | Daily",
            f"{user.mention}, Greg has blessed you with some pickles.",
            sections=[
                separator(),
                text_block(
                    "**Received**\n"
                    f"{format_currency(result.amount, config=config)}"
                ),
                text_block(
                    "**Wallet**\n"
                    f"{format_currency(result.account.wallet, config=config)}"
                ),
            ],
            accent_color=COLOR_PICKLE,
            footer="Do not ask where Greg got the pickles from...",
        )
    )
    return view

def work_view(
    user: discord.abc.User,
    result: WorkResult,
    config: BotConfig,
) -> discord.ui.LayoutView:
    view = discord.ui.LayoutView(timeout=60)
    view.add_item(
        make_container(
            "🧾 Greg | Work",
            f"{user.mention}, {result.work_message}",
            sections=[
                separator(),
                text_block(
                    "**Earned**\n"
                    f"{format_currency(result.amount, config=config)}"
                ),
                text_block(
                    "**Wallet**\n"
                    f"{format_currency(result.account.wallet, config=config)}"
                ),
            ],
            accent_color=COLOR_GREG,
            footer="Somehow this counts as employment.",
        )
    )
    return view

def cooldown_view(result: CooldownResult, config: BotConfig) -> discord.ui.LayoutView:
    return simple_view(
        "⏳ Whoa there cowboy!",
        (
            f"`{result.command_name}` is on cooldown.\n\n"
            f"Try again in **{format_seconds(result.remaining_seconds)}**.\n\n"
            f"Among popular belief, Greg is not made of pickles."
        ),
        accent_color=COLOR_WARNING,
        footer=PICKLE_FOOTER,
    )

def leaderboard_view(
    rows: list[LeaderboardEntry],
    config: BotConfig,
) -> discord.ui.LayoutView:
    if not rows:
        body = "Nobody has any pickles yet. Greg is disappointed but not surprised."
    else:
        lines: list[str] = []
        for index, row in enumerate(rows, start=1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(index, f"**#{index}**")
            lines.append(
                f"{medal} <@{row.user_id}>\n"
                f"{format_currency(row.net_worth, config=config)}"
            )
        body = "\n\n".join(lines)

    return simple_view(
        "🏆 Greg | Pickle Leaderboard",
        body,
        accent_color=COLOR_INFO,
        footer="Greg ranked the pickle hoarders.",
    )
from __future__ import annotations

from gregbot.config import BotConfig


def format_currency(amount: int, *, config: BotConfig) -> str:
    label = config.currency_singular if amount == 1 else config.currency_plural
    return f"{config.currency_emoji} {amount:,} {label}"
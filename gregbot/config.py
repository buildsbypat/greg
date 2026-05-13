from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

@dataclass(frozen=True)
class BotConfig:
    discord_token: str
    bot_prefix: str
    bot_name: str
    log_level: str
    database_path: Path
    currency_singular: str
    currency_plural: str
    currency_emoji: str

def load_config() -> BotConfig:
    load_dotenv()

    discord_token = os.getenv("DISCORD_TOKEN")
    if not discord_token:
        raise RuntimeError("Discord Token not found in .env")
    
    return BotConfig(
        discord_token=discord_token,
        bot_prefix=os.getenv("BOT_PREFIX", "!"),
        bot_name=os.getenv("BOT_NAME", "Greg"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        database_path=Path(os.getenv("DATABASE_PATH", "./data/greg.sqlite3")),
        currency_singular=os.getenv("CURRENCY_SINGULAR", "pickle"),
        currency_plural=os.getenv("CURRENCY_PLURAL", "pickles"),
        currency_emoji=os.getenv("CURRENCY_EMOJI", "🥒"),
    )
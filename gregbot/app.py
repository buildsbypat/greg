from __future__ import annotations

import logging
import sys

import discord
from discord.ext import commands

from gregbot.cogs.economy import EconomyCog
from gregbot.cogs.meta import MetaCog
from gregbot.config import BotConfig, load_config
from gregbot.database.connection import Database
from gregbot.logging_config import configure_logging
from gregbot.services.cooldown_service import CooldownService
from gregbot.services.economy_service import EconomyService
from gregbot.services.transaction_service import TransactionService

log = logging.getLogger(__name__)

class Greg(commands.Bot):
    def __init__(self, config: BotConfig, database: Database) -> None:
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=config.bot_prefix,
            intents=intents,
            help_command=None,
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=False,
                everyone=False,
            ),
        )

        self.config = config
        self.database = database
    
    async def setup_hook(self) -> None: 
        await self.database.initialize()

        transaction_service = TransactionService(self.database)
        cooldown_service = CooldownService(self.database)
        economy_service = EconomyService(
            database=self.database,
            cooldowns=cooldown_service,
            transactions=transaction_service,
            config=self.config,
        )

        await self.add_cog(MetaCog(self))
        await self.add_cog(EconomyCog(self, economy_service, self.config))

        synced = await self.tree.sync()
        log.info("⚠️ Synced %s slash command(s)", len(synced))
    
    async def on_ready(self) -> None:
        log.info("✅ Logged in as %s (ID: %s)", self.user.name, self.user.id)
    
    async def close(self) -> None:
        await self.database.close()
        await super().close()

def main() -> None:
    if sys.version_info < (3, 12):
        raise RuntimeError("⛔️ Python 3.12 twas not found. Greg feeds on Python 3.12.")
    
    config = load_config()
    configure_logging(config.log_level)

    database = Database(config.database_path)
    bot = Greg(config=config, database=database)
    bot.run(config.discord_token, log_handler=None)
from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import aiosqlite

from gregbot.config import BotConfig
from gregbot.database.connection import Database
from gregbot.models.economy import EconomyAccount
from gregbot.models.results import BalanceResult, CooldownResult, DailyResult,  LeaderboardEntry, WorkResult
from gregbot.services.cooldown_service import CooldownService
from gregbot.services.transaction_service import TransactionService

STARTING_WALLET = 100
STARTING_BANK = 0
DAILY_MIN = 150
DAILY_MAX = 1000
WORK_MIN = 50
WORK_MAX = 200

DAILY_COOLDOWN = timedelta(hours=24)
WORK_COOLDOWN = timedelta(minutes=15)

WORK_MESSAGES = (
    "Greg watched you pretend to work.",
    "You alphabetised Greg's imaginary paperwork.",
    "You found some pickles behind the vending machine.",
    "Greg gave you a clipboard and looked impressed.",
    "You fixed the office printer by looking disappointed at it.",
    "Greg asked you to sort the tiny paperwork. You survived.",
    "Greg's boss said he treats you too harshly.",
    "You scored some free pickles from the vending machine for kicking it a few times.",
    "The IT Department were impressed you fixed you're own issue.",
    "You were the only person to turn up to work today.",
    "Greg saw you actually work today. He was mildly impressed.",
)

class EconomyService:
    def __init__(
            self,
            *,
            database: Database,
            cooldowns: CooldownService,
            transactions: TransactionService,
            config: BotConfig,
    ) -> None:
        self.database = database
        self.cooldowns = cooldowns
        self.transactions = transactions
        self.config = config

    async def get_or_create_account(self, *, guild_id: str, user_id: str) -> EconomyAccount:
        account = await self.get_account(guild_id=guild_id, user_id=user_id)
        if account is not None: 
            return account

        now = datetime.now(UTC).isoformat()

        await self.database.connection.execute(
            """
            INSERT INTO economy_accounts (
                guild_id,
                user_id,
                wallet,
                bank,
                total_earned,
                total_spent,
                total_lost,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)
            """,
            (
                guild_id,
                user_id,
                STARTING_WALLET,
                STARTING_BANK,
                now,
                now,
            ),
        )
        await self.database.connection.commit()

        account = await self.get_account(guild_id=guild_id, user_id=user_id)
        if account is None:
            raise RuntimeError("Failed to create economy account.")
        
        await self.transactions.record(
            guild_id=guild_id,
            user_id=user_id,
            transaction_type="account_create",
            amount=STARTING_WALLET,
            account=account,
            description="Starting wallet balance.",
        )

        return account
    
    async def get_account(self, *, guild_id: str, user_id: str) -> EconomyAccount | None:
        async with self.database.connection.execute(
            """
            SELECT
                guild_id,
                user_id,
                wallet,
                bank,
                total_earned,
                total_spent,
                total_lost,
                created_at,
                updated_at
            FROM economy_accounts
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (guild_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return None
        
        return self._account_from_row(row)
    
    async def get_balance(self, *, guild_id: str, user_id: str) -> BalanceResult:
        account = await self.get_or_create_account(guild_id=guild_id, user_id=user_id)
        return BalanceResult(account=account)
    
    async def claim_daily(
            self,
            *,
            guild_id: str,
            user_id: str,
    ) -> DailyResult | CooldownResult:
        cooldown = await self.cooldowns.get_cooldown(
            guild_id=guild_id,
            user_id=user_id,
            command_name="daily",
        )
        if cooldown is not None:
            return cooldown
        
        amount = random.randint(DAILY_MIN, DAILY_MAX)
        account = await self._add_wallet(
            guild_id=guild_id,
            user_id=user_id,
            amount=amount,
            transaction_type="daily",
            description="Daily pickle claim.",
        )

        await self.cooldowns.set_cooldown(
            guild_id=guild_id,
            user_id=user_id,
            command_name="daily",
            duration=DAILY_COOLDOWN,
        )

        return DailyResult(
            account=account,
            amount=amount,
            streak=1,
        )
    
    async def work(
            self,
            *,
            guild_id: str,
            user_id: str,
    ) -> WorkResult | CooldownResult:
        cooldown = await self.cooldowns.get_cooldown(
            guild_id=guild_id,
            user_id=user_id,
            command_name="work",
        )
        if cooldown is not None:
            return cooldown
        
        amount = random.randint(WORK_MIN, WORK_MAX)
        work_message = random.choice(WORK_MESSAGES)

        account = await self._add_wallet(
            guild_id=guild_id,
            user_id=user_id,
            amount=amount,
            transaction_type="work",
            description=work_message,
        )

        await self.cooldowns.set_cooldown(
            guild_id=guild_id,
            user_id=user_id,
            command_name="work",
            duration=WORK_COOLDOWN,
        )

        return WorkResult(
            account=account,
            amount=amount,
            work_message=work_message,
        )
    
    async def get_leaderboard(self, *, guild_id: str, limit: int = 10) -> list[LeaderboardEntry]:
        async with self.database.connection.execute(
            """
            SELECT
                user_id,
                wallet,
                bank,
                wallet + bank AS net_worth
            FROM economy_accounts
            WHERE guild_id = ?
            ORDER BY net_worth DESC, wallet DESC, user_id ASC
            LIMIT ?
            """,
            (guild_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()

        return [
            LeaderboardEntry(
                user_id=str(row["user_id"]),
                wallet=int(row["wallet"]),
                bank=int(row["bank"]),
                net_worth=int(row["net_worth"])
            )
            for row in rows
        ]
    
    async def _add_wallet(
            self,
            *,
            guild_id: str,
            user_id: str,
            amount: int,
            transaction_type: str,
            description: str,
    ) -> EconomyAccount:
        await self.get_or_create_account(guild_id=guild_id, user_id=user_id)

        now = datetime.now(UTC).isoformat()

        await self.database.connection.execute(
            """
            UPDATE economy_accounts
            SET wallet = wallet + ?,
                total_earned = total_earned + ?,
                updated_at = ?
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (amount, amount, now, guild_id, user_id),
        )
        await self.database.connection.commit()

        account = await self.get_or_create_account(guild_id=guild_id, user_id=user_id)

        await self.transactions.record(
            guild_id=guild_id,
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            account=account,
            description=description,
        )

        return account
    
    @staticmethod
    def _account_from_row(row: aiosqlite.Row) -> EconomyAccount:
        return EconomyAccount(
                guild_id=str(row["guild_id"]),
                user_id=str(row["user_id"]),
                wallet=int(row["wallet"]),
                bank=int(row["bank"]),
                total_earned=int(row["total_earned"]),
                total_spent=int(row["total_spent"]),
                total_lost=int(row["total_lost"]),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
        )
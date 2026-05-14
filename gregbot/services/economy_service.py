from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import aiosqlite

from gregbot.config import BotConfig
from gregbot.database.connection import Database
from gregbot.models.economy import EconomyAccount
from gregbot.models.results import BalanceResult, CooldownResult, DailyResult,  LeaderboardEntry, WorkResult
from gregbot.models.jobs import Job
from gregbot.services.cooldown_service import CooldownService
from gregbot.services.transaction_service import TransactionService
from gregbot.utils.money import format_currency
from gregbot.services.jobs import JOBS

STARTING_WALLET = 100
STARTING_BANK = 0
DAILY_MIN = 150
DAILY_MAX = 1000
WORK_MIN = 50
WORK_MAX = 200
STARTING_JOB = None

DAILY_COOLDOWN = timedelta(hours=24)
WORK_COOLDOWN = timedelta(minutes=15)


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
                current_job,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, ?)
            """,
            (
                guild_id,
                user_id,
                STARTING_WALLET,
                STARTING_BANK,
                STARTING_WALLET,
                STARTING_JOB,
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
                current_job,
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
    
    async def get_job(self, key: str) -> Job | None:
        return next((job for job in JOBS if job.key == key), None)
    
    async def find_job(self, *, guild_id: str, user_id: str) -> Job:
        account = await self.get_or_create_account(guild_id=guild_id, user_id=user_id)

        available_jobs = list(JOBS)
        job = random.choice(available_jobs)

        now = datetime.now(UTC).isoformat()

        await self.database.connection.execute(
            """
            UPDATE economy_accounts
            SET current_job = ?,
                updated_at = ?
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (job.key, now, guild_id, user_id),
        )
        await self.database.connection.commit()

        return job
    
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
    ) -> WorkResult | CooldownResult | None:
        cooldown = await self.cooldowns.get_cooldown(
            guild_id=guild_id,
            user_id=user_id,
            command_name="work",
        )
        if cooldown is not None:
            return cooldown

        account = await self.get_or_create_account(guild_id=guild_id, user_id=user_id)

        if account.current_job is None:
            return None
        
        job = self._get_job(account.current_job)
        if job is None:
            return None
        
        amount = random.randint(job.min_pay, job.max_pay)
        message = random.choice(job.success_messages).format(amount=format_currency(amount, config=self.config))

        updated_account = await self._add_wallet(
            guild_id=guild_id,
            user_id=user_id,
            amount=amount,
            transaction_type="work",
            description=f"Worked as {job.name}",
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
            work_message=message,
            job_name=job.name,
            job_title=job.title,
            footer=random.choice(job.footers)
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
                current_job=str(row["current_job"]),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
        )
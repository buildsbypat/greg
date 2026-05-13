from __future__ import annotations

from datetime import UTC, datetime

from gregbot.database.connection import Database
from gregbot.models.economy import EconomyAccount


class TransactionService:
    def __init__(self, database: Database) -> None:
        self.database = database

        async def record(
                self,
                *,
                guild_id: str,
                user_id: str,
                transaction_type: str,
                amount: int,
                account: EconomyAccount,
                description: str,
                other_user_id: str | None = None,
        ) -> None:
            await self.database.connection.execute(
                """
                INSERT INTO economy_transactions (
                    guild_id,
                    user_id
                    other_user_id,
                    transaction_type,
                    amount,
                    wallet_after,
                    bank_after,
                    description,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    guild_id,
                    user_id,
                    other_user_id,
                    transaction_type,
                    amount,
                    account.wallet,
                    account.bank,
                    description,
                    datetime.now(UTC).isoformat(),
                ),
            )
            await self.database.connection.commit()
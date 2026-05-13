from __future__ import annotations

from datetime import UTC, datetime, timedelta

from gregbot.database.connection import Database
from gregbot.models.results import CooldownResult

class CooldownService:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def get_cooldown(
            self,
            *,
            guild_id: str,
            user_id: str,
            command_name: str,
    ) -> CooldownResult | None:
        now = datetime.now(UTC)

        async with self.database.connection.execute(
            """
            SELECT available_at
            FROM economy_cooldowns
            WHERE guild_id = ?
            AND user_id = ?
            AND command_name = ?
            """,
            (guild_id, user_id, command_name),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return None
        
        available_at = datetime.fromisoformat(str(row["available_at"]))
        if available_at <= now:
            return None
        
        remaining_seconds = max(0, round((available_at - now).total_seconds()))
        return CooldownResult(
            command_name=command_name,
            available_at=available_at,
            remaining_seconds=remaining_seconds,
        )
    
    async def set_cooldown(
            self,
            *,
            guild_id: str,
            user_id: str,
            command_name: str,
            duration: timedelta,
    ) -> datetime:
        available_at = datetime.now(UTC) + duration

        await self.database.connection.execute(
            """
            INSERT INTO economy_cooldowns (
                guild_id,
                user_id,
                command_name,
                available_at
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, command_name)
            DO UPDATE SET available_at = excluded.available_at
            """,
            (guild_id, user_id, command_name, available_at.isoformat()),
        )
        await self.database.connection.commit()

        return available_at
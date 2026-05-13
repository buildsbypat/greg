from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import Self

import aiosqlite

from gregbot.database.migrations import load_schema_sql

class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._connection: aiosqlite.Connection | None = None

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("⛔️ The Database, it is not initialised.")
        return self._connection
    
    async def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.path)
        self._connection.row_factory = aiosqlite.Row

        await self.connection.executescript(load_schema_sql())
        await self.connection.commit()

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def __aenter__(self) -> Self:
        await self.initialize()
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
        await self.close()
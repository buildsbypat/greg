from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class EconomyAccount:
    guild_id: str
    user_id: str
    wallet: int
    bank: int
    total_earned: int
    total_spent: int
    total_lost: int
    created_at: str
    updated_at: str

    @property
    def net_worth(self) -> int:
        return self.wallet + self.bank
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from gregbot.models.economy import EconomyAccount

@dataclass(frozen=True)
class CooldownResult:
    command_name: str
    available_at: datetime
    remaining_seconds: int

@dataclass(frozen=True)
class BalanceResult:
    account: EconomyAccount

@dataclass(frozen=True)
class DailyResult:
    account: EconomyAccount
    amount: int
    streak: int

@dataclass(frozen=True)
class WorkResult:
    account: EconomyAccount
    amount: int
    work_message: str
    job_name: str
    job_title: str
    footer: str

@dataclass(frozen=True)
class LeaderboardEntry:
    user_id: str
    wallet: int
    bank: int
    net_worth: int

@dataclass(frozen=True)
class FindJobResult:
    job_key: str
    job_name: str
    job_title: str
    min_pay: int
    max_pay: int
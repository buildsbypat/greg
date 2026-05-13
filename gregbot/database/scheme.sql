PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS scheme_version (
    version INTEGER PRIMARY KEY,
    applied_at TEST NOT NULL
);

CREATE TABLE IF NOT EXISTS economy_accounts (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    wallet INTEGER NOT NULL DEFAULT 0,
    bank INTEGER NOT NULL DEFAULT 0,
    total_earned INTEGER NOT NULL DEFAULT 0,
    total_spent INTEGER NOT NULL DEFAULT 0,
    total_lost INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS economy_cooldowns (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    command_name TEXT NOT NULL,
    available_at TEXT NOT NULL,
    PRIMARY KEY (guild_id, user_id, command_name)
);

CREATE TABLE IF NOT EXISTS economy_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    other_user_id TEXT,
    transaction_type TEXT NOT NULL,
    amount INTEGER NOT NULL,
    wallet_after INTEGER NOT NULL,
    bank_after INTEGER NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL
);
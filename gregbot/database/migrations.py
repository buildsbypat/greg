from __future__ import annotations

from pathlib import Path


def load_schema_spl() -> str:
    schema_path = Path(__file__).with_name("schema.sql")
    return schema_path.read_text(encoding="utf-8")
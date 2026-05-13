from __future__ import annotations

def format_seconds(seconds: int) -> str:
    if seconds <= 0:
        return "now"
    
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    parts: list[str] = []

    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs and not hours:
        parts.append(f"{secs}s")

    return " ".join(parts)
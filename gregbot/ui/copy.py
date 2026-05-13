from __future__ import annotations

SUCCESS_FOOTER = "Greg handled it. Surprisingly."
ERROR_FOOTER = "Greg doesn't know why it failed."
INFO_FOOTER = "Greg took this seriously. We promise."
PICKLE_FOOTER = "No pickles were hurt during this."

STATUS_LINES = (
    "Greg is making pickles.",
    "Greg has found a paperclip.",
    "Greg is looking busy.",
    "Greg is pondering.",
    "Greg has WHS concerns.",
    "Greg was never trained for this job.",
    "Greg is working just for the money.",
    "Greg is obviously not qualified for this.",
)

def footer(text: str) -> str:
    return text if text.startswith("-# ") else f"-# {text}"
from __future__ import annotations

import discord

from gregbot.ui import copy
from gregbot.ui.components import simple_view
from gregbot.ui.theme import COLOR_DANGER, COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING


def success_view(message: str, detail: str | None = None) -> discord.ui.LayoutView:
    body = message if detail is None else f"{message}\n\n{detail}"
    return simple_view(
        "✅ Greg | Success",
        body,
        accent_color=COLOR_SUCCESS,
        footer=copy.SUCCESS_FOOTER,
    )


def error_view(message: str, detail: str | None = None) -> discord.ui.LayoutView:
    body = message if detail is None else f"{message}\n\n{detail}"
    return simple_view(
        "⚠️ Greg | Problem",
        body,
        accent_color=COLOR_DANGER,
        footer=copy.ERROR_FOOTER,
    )


def warning_view(message: str, detail: str | None = None) -> discord.ui.LayoutView:
    body = message if detail is None else f"{message}\n\n{detail}"
    return simple_view(
        "⚠️ Greg | Warning",
        body,
        accent_color=COLOR_WARNING,
        footer=copy.ERROR_FOOTER,
    )


def info_view(message: str, detail: str | None = None) -> discord.ui.LayoutView:
    body = message if detail is None else f"{message}\n\n{detail}"
    return simple_view(
        "ℹ️ Greg | Info",
        body,
        accent_color=COLOR_INFO,
        footer=copy.INFO_FOOTER,
    )
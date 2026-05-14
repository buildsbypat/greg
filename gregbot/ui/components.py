from __future__ import annotations

from collections.abc import Iterable

import discord

from gregbot.ui.copy import footer as subtle_footer
from gregbot.ui.theme import COLOR_INFO


def _coerce_color(
    accent_color: discord.Colour | int | None,
) -> discord.Colour | int | None:
    if accent_color is None:
        return COLOR_INFO
    return discord.Colour(accent_color) if isinstance(accent_color, int) else accent_color


def text_block(text: str) -> discord.ui.TextDisplay:
    return discord.ui.TextDisplay(text)


def subtle(text: str) -> discord.ui.TextDisplay:
    return discord.ui.TextDisplay(subtle_footer(text))


def separator(*, visible: bool = True) -> discord.ui.Separator:
    return discord.ui.Separator(visible=visible)


def make_container(
    title: str,
    body: str | None = None,
    *,
    sections: Iterable[discord.ui.Item] | None = None,
    footer: str | None = None,
    accent_color: discord.Colour | int | None = None,
) -> discord.ui.Container:
    header = f"### {title}"
    if body:
        header = f"{header}\n\n{body}"

    items: list[discord.ui.Item] = [text_block(header)]

    if sections:
        items.extend(sections)

    if footer:
        items.append(separator())
        items.append(subtle(footer))

    return discord.ui.Container(*items, accent_color=_coerce_color(accent_color))


def simple_view(
    title: str,
    body: str | None = None,
    *,
    accent_color: discord.Colour | int | None = None,
    footer: str | None = None,
    timeout: float | None = 60,
) -> discord.ui.LayoutView:
    view = discord.ui.LayoutView(timeout=timeout)
    view.add_item(
        make_container(
            title,
            body,
            accent_color=accent_color,
            footer=footer,
        )
    )
    return view
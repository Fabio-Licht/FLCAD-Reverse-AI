"""Immutable settings for engineering viewport interaction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InteractionSettings:
    """Enable or disable independent engineering interaction behaviors."""

    enable_multi_selection: bool
    enable_context_menu: bool
    enable_hover_highlight: bool
    enable_inspector: bool

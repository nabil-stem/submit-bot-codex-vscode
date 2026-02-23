from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


ClickAction = Callable[[bool], bool]


@dataclass(frozen=True, slots=True)
class WindowIdentity:
    title: str
    process_name: str
    handle: int | None = None


@dataclass(slots=True)
class ButtonCandidate:
    window: WindowIdentity
    button_text: str
    enabled: bool
    near_text: str
    source: str
    click_action: ClickAction


@dataclass(slots=True)
class RuntimeState:
    paused: bool = False
    dry_run: bool = True
    last_click_ts: float | None = None
    last_match: str | None = None


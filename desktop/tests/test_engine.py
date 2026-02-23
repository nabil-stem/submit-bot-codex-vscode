from __future__ import annotations

import logging

from submit_autoclicker.config import AppConfig
from submit_autoclicker.core.engine import ClickEngine
from submit_autoclicker.models import ButtonCandidate, WindowIdentity


class FakeProvider:
    name = "fake"

    def __init__(self, candidates: list[ButtonCandidate]) -> None:
        self._candidates = candidates

    def scan(self, config: AppConfig) -> list[ButtonCandidate]:
        return list(self._candidates)


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def now(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _build_candidate(clicked: dict[str, int]) -> ButtonCandidate:
    def click_action(allow_focus: bool) -> bool:
        clicked["count"] += 1
        return True

    return ButtonCandidate(
        window=WindowIdentity(title="Visual Studio Code", process_name="Code.exe"),
        button_text="Submit",
        enabled=True,
        near_text="Do you want to make these changes?",
        source="fake",
        click_action=click_action,
    )


def _build_config(*, dry_run: bool, cooldown_ms: int = 5000) -> AppConfig:
    return AppConfig(
        allowed_processes=["Code.exe"],
        allowed_window_title_contains=["Visual Studio Code"],
        button_texts=["Submit"],
        poll_interval_ms=100,
        click_cooldown_ms=cooldown_ms,
        require_button_enabled=True,
        require_near_text_contains=[],
        allow_focus=False,
        dry_run=dry_run,
    )


def _logger() -> logging.Logger:
    logger = logging.getLogger("submit_autoclicker_test")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    return logger


def test_engine_dry_run_does_not_click() -> None:
    clicked = {"count": 0}
    candidate = _build_candidate(clicked)
    clock = FakeClock()
    engine = ClickEngine(
        config=_build_config(dry_run=True, cooldown_ms=1000),
        providers=[FakeProvider([candidate])],
        logger=_logger(),
        monotonic_fn=clock.now,
        wallclock_fn=clock.now,
    )

    matched = engine.run_once()

    assert matched is True
    assert clicked["count"] == 0
    assert engine.status()["last_click_ts"] is None


def test_engine_live_mode_clicks() -> None:
    clicked = {"count": 0}
    candidate = _build_candidate(clicked)
    clock = FakeClock()
    engine = ClickEngine(
        config=_build_config(dry_run=False, cooldown_ms=1000),
        providers=[FakeProvider([candidate])],
        logger=_logger(),
        monotonic_fn=clock.now,
        wallclock_fn=clock.now,
    )

    matched = engine.run_once()

    assert matched is True
    assert clicked["count"] == 1
    assert engine.status()["last_click_ts"] == 0.0


def test_engine_respects_cooldown() -> None:
    clicked = {"count": 0}
    candidate = _build_candidate(clicked)
    clock = FakeClock()
    engine = ClickEngine(
        config=_build_config(dry_run=False, cooldown_ms=5000),
        providers=[FakeProvider([candidate])],
        logger=_logger(),
        monotonic_fn=clock.now,
        wallclock_fn=clock.now,
    )

    assert engine.run_once() is True
    assert clicked["count"] == 1

    assert engine.run_once() is False
    assert clicked["count"] == 1

    clock.advance(5.0)
    assert engine.run_once() is True
    assert clicked["count"] == 2


from __future__ import annotations

import logging
import threading
import time
from collections.abc import Sequence
from typing import Protocol

from submit_autoclicker.config import AppConfig
from submit_autoclicker.core.policy import AllowlistPolicy, button_text_matches, near_text_matches
from submit_autoclicker.models import ButtonCandidate, RuntimeState


class CandidateProvider(Protocol):
    name: str

    def scan(self, config: AppConfig) -> Sequence[ButtonCandidate]:
        """Return button candidates discovered by this provider."""


class ClickEngine:
    def __init__(
        self,
        config: AppConfig,
        providers: Sequence[CandidateProvider],
        logger: logging.Logger,
        *,
        monotonic_fn=time.monotonic,
        wallclock_fn=time.time,
    ) -> None:
        self._config = config
        self._providers = list(providers)
        self._logger = logger
        self._state = RuntimeState(dry_run=config.dry_run)
        self._policy = AllowlistPolicy(config.allowed_processes, config.allowed_window_title_contains)
        self._monotonic_fn = monotonic_fn
        self._wallclock_fn = wallclock_fn

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_action_monotonic = float("-inf")

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, name="submit-autoclicker-loop", daemon=True)
            self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        with self._lock:
            thread = self._thread
        if thread:
            thread.join(timeout=timeout)

    def _run(self) -> None:
        self._logger.info("Click engine started.")
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                self._logger.exception("Unexpected engine loop error.")
            poll_seconds = self._snapshot_config().poll_interval_ms / 1000.0
            self._stop_event.wait(timeout=poll_seconds)
        self._logger.info("Click engine stopped.")

    def _snapshot_config(self) -> AppConfig:
        with self._lock:
            return self._config

    def _snapshot_state(self) -> RuntimeState:
        with self._lock:
            return RuntimeState(
                paused=self._state.paused,
                dry_run=self._state.dry_run,
                last_click_ts=self._state.last_click_ts,
                last_match=self._state.last_match,
            )

    def run_once(self) -> bool:
        config = self._snapshot_config()
        state = self._snapshot_state()

        if state.paused:
            return False

        now = self._monotonic_fn()
        cooldown_seconds = max(0, config.click_cooldown_ms) / 1000.0
        if now - self._last_action_monotonic < cooldown_seconds:
            return False

        selected_candidate: ButtonCandidate | None = None
        selected_provider_name = ""

        for provider in self._providers:
            try:
                candidates = provider.scan(config)
            except Exception:
                self._logger.exception("Provider '%s' scan failed.", provider.name)
                continue

            for candidate in candidates:
                if not self._policy.is_allowed(candidate.window):
                    continue
                if config.require_button_enabled and not candidate.enabled:
                    continue
                if not button_text_matches(candidate.button_text, config.button_texts):
                    continue
                if not near_text_matches(candidate.near_text, config.require_near_text_contains):
                    continue
                selected_candidate = candidate
                selected_provider_name = provider.name
                break
            if selected_candidate:
                break

        if not selected_candidate:
            return False

        match_summary = (
            f"provider={selected_provider_name} "
            f"process={selected_candidate.window.process_name} "
            f"title={selected_candidate.window.title!r} "
            f"button={selected_candidate.button_text!r}"
        )

        with self._lock:
            self._state.last_match = match_summary

        if state.dry_run:
            self._last_action_monotonic = now
            self._logger.info("Dry-run: matched candidate. %s", match_summary)
            return True

        try:
            clicked = selected_candidate.click_action(config.allow_focus)
        except Exception:
            self._logger.exception("Click action failed unexpectedly. %s", match_summary)
            clicked = False

        if clicked:
            self._last_action_monotonic = now
            with self._lock:
                self._state.last_click_ts = self._wallclock_fn()
            self._logger.info("Clicked candidate. %s", match_summary)
            return True

        self._logger.warning("Candidate matched but click did not execute. %s", match_summary)
        return False

    def toggle_paused(self) -> bool:
        with self._lock:
            self._state.paused = not self._state.paused
            return self._state.paused

    def toggle_dry_run(self) -> bool:
        with self._lock:
            self._state.dry_run = not self._state.dry_run
            return self._state.dry_run

    def set_dry_run(self, enabled: bool) -> None:
        with self._lock:
            self._state.dry_run = enabled

    def update_config(self, config: AppConfig, keep_runtime_toggles: bool = True) -> None:
        with self._lock:
            previous_state = RuntimeState(
                paused=self._state.paused,
                dry_run=self._state.dry_run,
                last_click_ts=self._state.last_click_ts,
                last_match=self._state.last_match,
            )
            self._config = config
            self._policy = AllowlistPolicy(config.allowed_processes, config.allowed_window_title_contains)
            if keep_runtime_toggles:
                self._state.paused = previous_state.paused
                self._state.dry_run = previous_state.dry_run
                self._state.last_click_ts = previous_state.last_click_ts
                self._state.last_match = previous_state.last_match
            else:
                self._state.dry_run = config.dry_run
                self._state.paused = False

    def status(self) -> dict[str, str | bool | float | None]:
        with self._lock:
            return {
                "paused": self._state.paused,
                "dry_run": self._state.dry_run,
                "last_click_ts": self._state.last_click_ts,
                "last_match": self._state.last_match,
                "poll_interval_ms": self._config.poll_interval_ms,
                "click_cooldown_ms": self._config.click_cooldown_ms,
            }

from __future__ import annotations

import re

from submit_autoclicker.models import WindowIdentity


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def button_text_matches(candidate_text: str, configured_patterns: list[str]) -> bool:
    normalized_candidate = normalize_text(candidate_text)
    if not normalized_candidate:
        return False

    for pattern in configured_patterns:
        normalized_pattern = normalize_text(pattern)
        if not normalized_pattern:
            continue
        if normalized_candidate == normalized_pattern:
            return True
        if not normalized_candidate.startswith(normalized_pattern):
            continue

        # Allow "pattern + delimiter", e.g. "Submit ⏎", "Yes, and don't ask again".
        if len(normalized_candidate) > len(normalized_pattern):
            next_char = normalized_candidate[len(normalized_pattern)]
            if not next_char.isalnum():
                return True
        else:
            return True
    return False


def near_text_matches(near_text: str, required_near_patterns: list[str]) -> bool:
    if not required_near_patterns:
        return True

    normalized_near_text = normalize_text(near_text)
    if not normalized_near_text:
        return False

    return any(
        normalize_text(pattern) and normalize_text(pattern) in normalized_near_text
        for pattern in required_near_patterns
    )


class AllowlistPolicy:
    def __init__(self, allowed_processes: list[str], allowed_title_contains: list[str]) -> None:
        self._allowed_processes = {normalize_text(item) for item in allowed_processes if normalize_text(item)}
        self._allowed_title_contains = [
            normalize_text(item) for item in allowed_title_contains if normalize_text(item)
        ]

    def is_allowed(self, window: WindowIdentity) -> bool:
        process_name = normalize_text(window.process_name)
        title = normalize_text(window.title)

        if self._allowed_processes and process_name not in self._allowed_processes:
            return False

        if self._allowed_title_contains and not any(
            needle in title for needle in self._allowed_title_contains
        ):
            return False

        return True

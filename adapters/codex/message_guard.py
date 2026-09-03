"""Dependency-free message ordering and token-ceiling guard for Codex dispatch."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from typing import Any


_SCHEMA_VERSION = "dispatch-guard/1"
_FEATURE_ID = "dispatch-message-guard"
_FEATURE_VERSION = "1.0.0"
_MAX_PLATFORM_CONTEXT_WINDOW = 272_000
_MESSAGE_KEYS = {"role", "content"}
_HISTORY_ROLES = {"user", "assistant"}


class DispatchGuardError(ValueError):
    """Privacy-safe, fail-closed dispatch guard error."""

    __slots__ = (
        "code",
        "token_count",
        "token_ceiling",
        "prefix_digest",
        "decision",
    )

    def __init__(
        self,
        code: str,
        field: str,
        *,
        token_count: int | None = None,
        token_ceiling: int | None = None,
        prefix_digest: str | None = None,
    ) -> None:
        super().__init__(f"{code}: invalid {field}")
        self.code = code
        self.token_count = token_count
        self.token_ceiling = token_ceiling
        self.prefix_digest = prefix_digest
        self.decision = "REJECT"


def _reject(
    code: str,
    field: str,
    *,
    token_count: int | None = None,
    token_ceiling: int | None = None,
    prefix_digest: str | None = None,
) -> None:
    raise DispatchGuardError(
        code,
        field,
        token_count=token_count,
        token_ceiling=token_ceiling,
        prefix_digest=prefix_digest,
    )


def _require_nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or value == "":
        _reject("DMG-SCHEMA", field)
    return value


def _copy_history(
    chat_history: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    if isinstance(chat_history, (str, bytes)) or not isinstance(
        chat_history, Sequence
    ):
        _reject("DMG-SCHEMA", "chat_history")

    copied: list[dict[str, str]] = []
    try:
        for entry in chat_history:
            if not isinstance(entry, Mapping) or set(entry.keys()) != _MESSAGE_KEYS:
                _reject("DMG-SCHEMA", "chat_history entry")
            role = entry["role"]
            content = entry["content"]
            if role == "system":
                _reject("DMG-HISTORY-SYSTEM", "chat_history role")
            if role not in _HISTORY_ROLES:
                _reject("DMG-SCHEMA", "chat_history role")
            if not isinstance(content, str) or content == "":
                _reject("DMG-SCHEMA", "chat_history content")
            copied.append({"role": role, "content": content})
    except DispatchGuardError:
        raise
    except Exception:
        _reject("DMG-SCHEMA", "chat_history")
    return copied


def _prefix_digest(
    prefix_template_version: str, prefix_messages: list[dict[str, str]]
) -> str:
    prefix_object = {
        "template_version": prefix_template_version,
        "messages": prefix_messages,
    }
    try:
        canonical_bytes = json.dumps(
            prefix_object,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    except Exception:
        _reject("DMG-PREFIX", "static prefix")
    return "sha256:" + hashlib.sha256(canonical_bytes).hexdigest()


def _messages_match_snapshot(
    messages: object, snapshot: list[dict[str, str]]
) -> bool:
    if not isinstance(messages, list) or len(messages) != len(snapshot):
        return False
    for actual, expected in zip(messages, snapshot):
        if not isinstance(actual, dict):
            return False
        if set(actual.keys()) != _MESSAGE_KEYS or actual != expected:
            return False
    return True


def build_guarded_messages(
    static_system_prompt: str,
    codebase_structure: str,
    chat_history: Sequence[Mapping[str, str]],
    active_request: str,
    token_counter: Callable[[Sequence[Mapping[str, str]]], int],
    *,
    prefix_template_version: str = "1.0.0",
    platform_context_window: int = 272_000,
    reserve_tokens: int = 12_000,
    max_tokens: int | None = None,
) -> dict[str, object]:
    """Build a stable-prefix message array and reject unsafe dispatches."""

    valid_window = (
        type(platform_context_window) is int
        and 1 <= platform_context_window <= _MAX_PLATFORM_CONTEXT_WINDOW
    )
    valid_reserve = (
        type(reserve_tokens) is int
        and reserve_tokens > 0
        and valid_window
        and reserve_tokens < platform_context_window
    )
    derived_ceiling = (
        platform_context_window - reserve_tokens
        if valid_window and valid_reserve
        else None
    )
    valid_max = (
        max_tokens is None
        or (
            type(max_tokens) is int
            and derived_ceiling is not None
            and 1 <= max_tokens <= derived_ceiling
        )
    )
    if not valid_window or not valid_reserve or not valid_max:
        invalid_ceiling = max_tokens if type(max_tokens) is int else None
        _reject(
            "DMG-TOKEN-CEILING",
            "token ceiling configuration",
            token_ceiling=invalid_ceiling,
        )
    assert derived_ceiling is not None
    effective_ceiling = derived_ceiling if max_tokens is None else max_tokens

    static_system_prompt = _require_nonempty_string(
        static_system_prompt, "static_system_prompt"
    )
    codebase_structure = _require_nonempty_string(
        codebase_structure, "codebase_structure"
    )
    active_request = _require_nonempty_string(active_request, "active_request")
    prefix_template_version = _require_nonempty_string(
        prefix_template_version, "prefix_template_version"
    )
    history = _copy_history(chat_history)

    if not callable(token_counter):
        _reject(
            "DMG-COUNTER-MISSING",
            "token_counter",
            token_ceiling=effective_ceiling,
        )

    prefix_messages = [
        {"role": "system", "content": static_system_prompt},
        {"role": "system", "content": codebase_structure},
    ]
    prefix_digest = _prefix_digest(prefix_template_version, prefix_messages)
    messages = [
        *prefix_messages,
        *history,
        {"role": "user", "content": active_request},
    ]
    snapshot = [dict(message) for message in messages]

    try:
        token_count: Any = token_counter(messages)
    except Exception:
        _reject(
            "DMG-COUNTER-FAILED",
            "token_counter",
            token_ceiling=effective_ceiling,
            prefix_digest=prefix_digest,
        )

    if not _messages_match_snapshot(messages, snapshot):
        _reject(
            "DMG-ORDER",
            "counter-mutated messages",
            token_ceiling=effective_ceiling,
            prefix_digest=prefix_digest,
        )
    if isinstance(token_count, bool) or not isinstance(token_count, int) or token_count < 0:
        _reject(
            "DMG-COUNTER-INVALID",
            "token_counter result",
            token_ceiling=effective_ceiling,
            prefix_digest=prefix_digest,
        )
    if token_count >= effective_ceiling:
        _reject(
            "DMG-LIMIT",
            "token limit",
            token_count=token_count,
            token_ceiling=effective_ceiling,
            prefix_digest=prefix_digest,
        )

    return {
        "schema_version": _SCHEMA_VERSION,
        "feature_id": _FEATURE_ID,
        "feature_version": _FEATURE_VERSION,
        "prefix_template_version": prefix_template_version,
        "prefix_digest": prefix_digest,
        "messages": messages,
        "platform_context_window": platform_context_window,
        "reserve_tokens": reserve_tokens,
        "token_count": token_count,
        "token_ceiling": effective_ceiling,
        "decision": "ALLOW",
    }

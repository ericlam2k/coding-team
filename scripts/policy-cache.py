#!/usr/bin/env python3
"""Track a session-local cache for stable coding-team policy files.

The cache stores only file metadata and SHA-256 digests.  It does not replace
the host's injected skill text, system instructions, human gates, or the
per-delegation role-card preflight.  ``check`` reuses unchanged files and
returns a non-zero status when the Lead must refresh the policy bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path.cwd().resolve()
CACHE_PATH = PROJECT_ROOT / ".coding-team" / "cache" / "policy-manifest.json"
EVENT_LOG_PATH = PROJECT_ROOT / ".coding-team" / "runs" / "policy-cache-events.jsonl"
SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")
CONTEXT_FINGERPRINT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

BASE_POLICY_FILES = (
    "AGENTS.md",
    "adapters/codex/SKILL.md",
    "adapters/codex/runtime.md",
    "adapters/codex/model-pool.map.md",
    "adapters/codex/role-model-lock.json",
    "core/orchestration.md",
    "core/model-routing.md",
    "core/concurrency.md",
    "core/human-gates.md",
    "core/policy-cache.md",
    "core/adaptive-timing.md",
)
LEARNING_POLICY_FILE = "core/learning-and-distillation.md"
LOCAL_DATA_BOUNDARY = {
    "storage_scope": "LOCAL_ONLY",
    "export_status": "NOT_REQUESTED",
    "public_safe": False,
    "consent_ref": None,
    "redaction_check": "NOT_RUN",
}
ADAPTER_POLICY_SCOPE = "codex-local-policy"


class CacheError(Exception):
    """A safe, user-facing cache error."""


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def session_id(raw: str | None) -> str | None:
    value = (raw or os.environ.get("WYSY_POLICY_SESSION_ID") or "").strip()
    if not value:
        return None
    if value == "UNAVAILABLE":
        raise CacheError("session id cannot use the reserved UNAVAILABLE sentinel")
    if not SESSION_ID_RE.fullmatch(value):
        raise CacheError("session id must contain only letters, digits, '.', '_', ':', or '-'")
    return value


def context_fingerprint(raw: str | None) -> str | None:
    """Resolve the host's opaque active-context identity.

    The repository cannot detect a Codex context compaction by itself.  A
    missing fingerprint therefore fails closed to ``BYPASSED`` instead of
    pretending that a local manifest is still safe to reuse.
    """
    value = (raw or os.environ.get("WYSY_POLICY_CONTEXT_FINGERPRINT") or "").strip()
    if not value:
        return None
    if value == "UNAVAILABLE":
        raise CacheError("context fingerprint cannot use the reserved UNAVAILABLE sentinel")
    if not CONTEXT_FINGERPRINT_RE.fullmatch(value):
        raise CacheError(
            "context fingerprint must contain only letters, digits, '.', '_', ':', or '-'")
    return value


def run_id(raw: str | None) -> str | None:
    value = (raw or "").strip()
    if not value:
        return None
    if not RUN_ID_RE.fullmatch(value):
        raise CacheError("run id must contain only letters, digits, '.', '_', ':', or '-'")
    return value


def manifest_revision() -> str:
    value = os.environ.get("WYSY_POLICY_MANIFEST_REVISION", "UNAVAILABLE").strip()
    if value == "UNAVAILABLE":
        return value
    if not RUN_ID_RE.fullmatch(value):
        raise CacheError("manifest revision must be an opaque safe identifier")
    return value


def coding_team_root(raw: str | None) -> tuple[Path, str]:
    configured = (raw or os.environ.get("CODING_TEAM_ROOT") or "").strip()
    if configured:
        root = Path(configured).expanduser().resolve()
        source = "env:CODING_TEAM_ROOT"
    else:
        root = (PROJECT_ROOT / "coding-team").resolve()
        source = "repo-local:coding-team"
    if not root.is_dir():
        raise CacheError(f"coding-team root does not exist: {root}")
    # Keep the source label sanitized while preventing two different policy
    # roots with identical bytes from sharing a manifest by accident.
    root_fingerprint = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:16]
    return root, f"{source}:{root_fingerprint}"


def policy_paths(root: Path, include_learning: bool) -> list[Path]:
    names = list(BASE_POLICY_FILES)
    if include_learning:
        names.append(LEARNING_POLICY_FILE)
    paths = [root / name for name in names]
    missing = [path.relative_to(root).as_posix() for path in paths if not path.is_file()]
    if missing:
        raise CacheError("missing policy files: " + ", ".join(missing))
    return paths


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_meta(path: Path, root: Path, *, include_digest: bool) -> dict[str, Any]:
    stat = path.stat()
    item: dict[str, Any] = {
        "path": path.relative_to(root).as_posix(),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }
    if include_digest:
        item["sha256"] = digest(path)
    return item


def load_manifest() -> dict[str, Any] | None:
    if not CACHE_PATH.is_file():
        return None
    try:
        value = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CacheError(f"invalid policy manifest: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise CacheError("policy manifest schema is unsupported")
    return value


def write_manifest(value: dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_event(summary: dict[str, Any], *, sid: str | None, run_id: str | None) -> None:
    EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    event_id = uuid.uuid4().hex
    event = {
        **summary,
        "event_id": event_id,
        "run_id": run_id or f"local-{event_id[:12]}",
        "session_id": sid or "UNAVAILABLE",
        "event_type": "POLICY_MANIFEST_CACHE",
        "observed_at": now(),
        "policy_cache": summary["policy_cache"],
        "timing": summary["timing"],
        "token_status": summary["token_status"],
        "auto_action": "none",
        "data_boundary": LOCAL_DATA_BOUNDARY,
        # Keep the compact helper receipt for existing local consumers.
        "recorded_at": now(),
    }
    with EVENT_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def telemetry(elapsed: float) -> dict[str, Any]:
    # The local helper can measure its own process time.  It cannot see model
    # input/output tokens or provider billing, so those remain explicit.
    return {
        "elapsed_seconds": round(elapsed, 6),
        "elapsed_source": "local policy-cache helper",
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
        "token_status": "unavailable",
        "token_source": "no host/runtime telemetry supplied",
        "currency_status": "unavailable",
        "currency_source": "no provider/rate source supplied",
    }


def manifest_identity(files: list[dict[str, Any]]) -> tuple[str, str]:
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest_hash = hashlib.sha256(canonical).hexdigest()
    return f"manifest_{manifest_hash[:16]}", manifest_hash


def policy_cache_record(
    *,
    status: str,
    sid: str | None,
    context: str | None,
    manifest: dict[str, Any] | None,
    reason: str,
    observed_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": status,
        "session_id": sid or "UNAVAILABLE",
        "context_fingerprint": context or "UNAVAILABLE",
        "adapter_policy_scope": (manifest or {}).get("adapter_policy_scope", "UNAVAILABLE"),
        "manifest_id": (manifest or {}).get("manifest_id", "UNAVAILABLE"),
        "manifest_revision": (manifest or {}).get("manifest_revision", "UNAVAILABLE"),
        "manifest_hash_sha256": (manifest or {}).get("manifest_hash_sha256", "UNAVAILABLE"),
        "reason": reason,
        "observed_at": observed_at,
    }


def build_summary(
    *,
    sid: str | None,
    context: str | None,
    status: str,
    raw_status: str,
    root_source: str,
    paths: list[Path],
    read_count: int,
    reused: int,
    invalidated: list[str],
    manifest: dict[str, Any] | None,
    reason: str,
    elapsed: float,
    timing_field: str,
    hashed: int = 0,
) -> dict[str, Any]:
    observed_at = now()
    old_telemetry = telemetry(elapsed)
    token_status = {
        "status": "UNAVAILABLE",
        "input_tokens": None,
        "output_tokens": None,
        "cached_input_tokens": None,
        "source": None,
        "units": None,
    }
    return {
        "session_id": sid,
        "status": raw_status,
        "canonical_status": status,
        "manifest_ref": ".coding-team/cache/policy-manifest.json",
        "root_source": root_source,
        "session_status": "MATCHED" if sid else "UNAVAILABLE",
        "context_status": "MATCHED" if context else "UNAVAILABLE",
        "policy_files_declared": len(paths),
        "policy_files_read": read_count,
        "policy_files_reused": reused,
        "policy_files_hashed": hashed,
        "invalidated_files": sorted(set(invalidated)),
        "reason": reason,
        "policy_cache": policy_cache_record(
            status=status,
            sid=sid,
            context=context,
            manifest=manifest,
            reason=reason,
            observed_at=observed_at,
        ),
        "timing": {
            "status": "MEASURED",
            "manifest_read_ms": round(elapsed * 1000, 3) if timing_field == "manifest_read_ms" else None,
            "cache_lookup_ms": round(elapsed * 1000, 3) if timing_field == "cache_lookup_ms" else None,
            "source": "local policy-cache helper",
        },
        "token_status": token_status,
        "telemetry": old_telemetry,
    }


def refresh(
    args: argparse.Namespace,
    sid: str,
    context: str | None,
    root: Path,
    root_source: str,
    paths: list[Path],
    started: float,
) -> dict[str, Any]:
    if sid is None or context is None:
        return build_summary(
            sid=sid,
            context=context,
            status="BYPASSED",
            raw_status="BYPASSED",
            root_source=root_source,
            paths=paths,
            read_count=0,
            reused=0,
            invalidated=[],
            manifest=None,
            reason="session or context identity unavailable; cache not initialized",
            elapsed=time.perf_counter() - started,
            timing_field="manifest_read_ms",
        )
    files = [file_meta(path, root, include_digest=True) for path in paths]
    manifest_id, manifest_hash = manifest_identity(files)
    manifest = {
        "schema_version": 1,
        "session_id": sid,
        "context_fingerprint": context or "UNAVAILABLE",
        "root_source": root_source,
        "adapter_policy_scope": ADAPTER_POLICY_SCOPE,
        "manifest_id": manifest_id,
        "manifest_revision": manifest_revision(),
        "manifest_hash_sha256": manifest_hash,
        "include_learning_policy": args.include_learning,
        "loaded_at": now(),
        "files": files,
    }
    write_manifest(manifest)
    elapsed = time.perf_counter() - started
    return build_summary(
        sid=sid,
        context=context,
        status="MISS" if context else "BYPASSED",
        raw_status="LOADED" if context else "BYPASSED",
        root_source=root_source,
        paths=paths,
        read_count=len(paths),
        reused=0,
        invalidated=[],
        manifest=manifest,
        reason="fresh manifest read" if context else "context fingerprint unavailable",
        elapsed=elapsed,
        timing_field="manifest_read_ms",
    )


def check(
    args: argparse.Namespace,
    sid: str,
    context: str | None,
    root: Path,
    root_source: str,
    paths: list[Path],
    started: float,
) -> tuple[dict[str, Any], int]:
    manifest_error: str | None = None
    try:
        manifest = load_manifest()
    except CacheError as exc:
        manifest = None
        manifest_error = str(exc)
    invalidated: list[str] = []
    read_count = 0
    reused = 0
    hashed_count = 0
    if manifest_error:
        summary = build_summary(
            sid=sid,
            context=context,
            status="UNAVAILABLE",
            raw_status="UNAVAILABLE",
            root_source=root_source,
            paths=paths,
            read_count=0,
            reused=0,
            hashed=0,
            invalidated=["manifest unreadable"],
            manifest=None,
            reason=manifest_error,
            elapsed=time.perf_counter() - started,
            timing_field="cache_lookup_ms",
        )
        return summary, 1
    if sid is None or context is None:
        if manifest is None:
            invalidated.append("manifest missing")
        summary = build_summary(
            sid=sid,
            context=context,
            status="BYPASSED",
            raw_status="BYPASSED",
            root_source=root_source,
            paths=paths,
            read_count=0,
            reused=0,
            hashed=0,
            invalidated=invalidated,
            manifest=manifest,
            reason="session or context identity unavailable; refresh is required",
            elapsed=time.perf_counter() - started,
            timing_field="cache_lookup_ms",
        )
        return summary, 1
    if manifest is None:
        invalidated.append("manifest missing")
    else:
        if manifest.get("session_id") != sid:
            invalidated.append("session changed")
        if manifest.get("context_fingerprint") != context:
            invalidated.append("context changed or lost")
        if manifest.get("root_source") != root_source:
            invalidated.append("policy root changed")
        if manifest.get("adapter_policy_scope") != ADAPTER_POLICY_SCOPE:
            invalidated.append("adapter policy scope changed")
        if manifest.get("manifest_revision") != manifest_revision():
            invalidated.append("manifest revision changed")
        if bool(manifest.get("include_learning_policy")) != bool(args.include_learning):
            invalidated.append("learning-policy selection changed")
        previous = {item.get("path"): item for item in manifest.get("files", []) if isinstance(item, dict)}
        for path in paths:
            relative = path.relative_to(root).as_posix()
            prior = previous.get(relative)
            current = file_meta(path, root, include_digest=True)
            hashed_count += 1
            if not prior:
                invalidated.append(relative)
                read_count += 1
                continue
            if (
                current.get("size") != prior.get("size")
                or current.get("mtime_ns") != prior.get("mtime_ns")
                or current.get("sha256") != prior.get("sha256")
            ):
                read_count += 1
                if current.get("sha256") != prior.get("sha256"):
                    invalidated.append(relative)
            else:
                reused += 1
        if set(previous) != {path.relative_to(root).as_posix() for path in paths}:
            invalidated.append("policy file set changed")
    if manifest is None:
        status = "MISS"
        raw_status = "MISS"
        reason = "manifest missing; fresh manifest read is required"
    else:
        status = "HIT" if not invalidated else "INVALIDATED"
        raw_status = "CACHE_HIT" if status == "HIT" else "INVALIDATED"
        reason = (
            "matching session/context and policy manifest"
            if status == "HIT"
            else "policy manifest identity changed"
        )
    summary = build_summary(
        sid=sid,
        context=context,
        status=status,
        raw_status=raw_status,
        root_source=root_source,
        paths=paths,
        read_count=read_count,
        reused=reused,
        hashed=hashed_count,
        invalidated=invalidated,
        manifest=manifest,
        reason=reason,
        elapsed=time.perf_counter() - started,
        timing_field="cache_lookup_ms",
    )
    return summary, 0 if status == "HIT" else 1


def print_summary(summary: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return
    telemetry_data = summary["telemetry"]
    print(
        "policy_cache={status} session={session_id} read={policy_files_read} "
        "reused={policy_files_reused} hashed={policy_files_hashed} "
        "elapsed_seconds={elapsed} tokens={tokens}".format(
            status=summary["canonical_status"],
            session_id=summary["session_id"],
            policy_files_read=summary["policy_files_read"],
            policy_files_reused=summary["policy_files_reused"],
            policy_files_hashed=summary["policy_files_hashed"],
            elapsed=telemetry_data["elapsed_seconds"],
            tokens=telemetry_data["token_status"],
        )
    )
    if summary["invalidated_files"]:
        print("invalidated: " + ", ".join(summary["invalidated_files"]))
    print("reason: " + summary["reason"])
    print("manifest: " + summary["manifest_ref"])
    print("token/currency telemetry: unavailable (host/runtime receipt not supplied)")


def safe_failure_reason(exc: Exception) -> str:
    """Return a stable, non-sensitive reason for a local Monitor event."""
    message = str(exc).lower()
    if "missing policy files" in message:
        return "policy files unavailable"
    if "invalid policy manifest" in message or "manifest schema" in message:
        return "policy manifest unreadable"
    if "coding-team root" in message:
        return "coding-team root unavailable"
    if isinstance(exc, OSError):
        return "local cache I/O unavailable"
    return "policy cache command unavailable"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "refresh", "check"))
    parser.add_argument("--session-id")
    parser.add_argument("--context-fingerprint")
    parser.add_argument("--run-id")
    parser.add_argument("--coding-team-root")
    parser.add_argument("--include-learning", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-record", action="store_true", help="do not append a local Monitor event")
    args = parser.parse_args()
    started = time.perf_counter()
    sid: str | None = None
    context: str | None = None
    event_run_id: str | None = None
    root_source = "unavailable"
    try:
        sid = session_id(args.session_id)
        context = context_fingerprint(args.context_fingerprint)
        event_run_id = run_id(args.run_id)
        root, root_source = coding_team_root(args.coding_team_root)
        paths = policy_paths(root, args.include_learning)
        if args.command in {"init", "refresh"}:
            summary = refresh(args, sid, context, root, root_source, paths, started)
            exit_code = 0 if summary["canonical_status"] == "MISS" else 1
        else:
            summary, exit_code = check(args, sid, context, root, root_source, paths, started)
        if not args.no_record:
            append_event(summary, sid=sid, run_id=event_run_id)
        print_summary(summary, args.json)
        return exit_code
    except (CacheError, OSError) as exc:
        if not args.no_record:
            summary = build_summary(
                sid=sid,
                context=context,
                status="UNAVAILABLE",
                raw_status="UNAVAILABLE",
                root_source=root_source,
                paths=[],
                read_count=0,
                reused=0,
                invalidated=["policy cache command unavailable"],
                manifest=None,
                reason=safe_failure_reason(exc),
                elapsed=time.perf_counter() - started,
                timing_field="manifest_read_ms",
            )
            try:
                append_event(summary, sid=sid, run_id=event_run_id)
            except OSError:
                pass
            print_summary(summary, args.json)
        else:
            print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

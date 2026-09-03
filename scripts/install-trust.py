#!/usr/bin/env python3
"""Issue and verify a bounded Coding Team installation receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


CONTRACT_VERSION = 1
STATUS = "VERIFIED_INSTALL"
COMMON_AUTHORITY = (
    "bin/ct",
    "core/orchestration.md",
    "core/model-routing.md",
    "core/concurrency.md",
    "core/human-gates.md",
    "core/qa-operating-model.md",
    "install.sh",
    "core/adaptive-timing.md",
    "scripts/install-coding-team.sh",
    "scripts/install-trust.py",
    "skills/quality/qa-evidence-enforcement/SKILL.md",
)


class TrustError(ValueError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _authority_paths(root: Path, platform: str) -> tuple[str, ...]:
    paths = list(COMMON_AUTHORITY)
    paths.append(f"adapters/{platform}/SKILL.md")
    if platform == "codex":
        paths.extend(
            (
                "adapters/codex/runtime.md",
                "adapters/codex/framework-reload.md",
                "adapters/codex/scripts/prepare-dispatch.py",
                "adapters/codex/scripts/check-install.py",
            )
        )
    role_dir = root / "core" / "roles"
    paths.extend(path.relative_to(root).as_posix() for path in sorted(role_dir.glob("*.md")))
    result = tuple(sorted(set(paths)))
    if not result or len(result) > 64:
        raise TrustError("authority set is empty or exceeds the 64-file bound")
    return result


def _manifest(root: Path, platform: str) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for relative in _authority_paths(root, platform):
        path = root / relative
        if not path.is_file():
            raise TrustError(f"missing authority file: {relative}")
        manifest[relative] = _sha256(path)
    return manifest


def _compatibility_id(manifest: dict[str, str]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _link_evidence(root: Path, platform: str, adapter_dst: Path, qa_dst: Path) -> dict[str, str]:
    expected_adapter = (root / "adapters" / platform).resolve(strict=True)
    expected_qa = (root / "skills" / "quality" / "qa-evidence-enforcement").resolve(strict=True)
    evidence: dict[str, str] = {}
    for name, destination, expected in (
        ("adapter", adapter_dst, expected_adapter),
        ("conditional_qa", qa_dst, expected_qa),
    ):
        if not destination.is_symlink():
            raise TrustError(f"{name} activation is not a symlink: {destination}")
        try:
            actual = (destination.parent / os.readlink(destination)).resolve(strict=True)
        except OSError as exc:
            raise TrustError(f"{name} activation target is unreadable") from exc
        if actual != expected:
            raise TrustError(f"{name} activation target mismatch")
        evidence[f"{name}_destination"] = str(destination.absolute())
        evidence[f"{name}_target"] = str(actual)
    evidence["result"] = "PASS"
    return evidence


def _write_atomic(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def issue(
    root: Path, platform: str, receipt: Path, adapter_dst: Path, qa_dst: Path
) -> dict[str, object]:
    root = root.resolve(strict=True)
    manifest = _manifest(root, platform)
    activation = _link_evidence(root, platform, adapter_dst, qa_dst)
    value: dict[str, object] = {
        "contract_version": CONTRACT_VERSION,
        "status": STATUS,
        "installed_root": str(root),
        "platform": platform,
        "compatibility_id": _compatibility_id(manifest),
        "authority_manifest": manifest,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "validation": {
            "required_authority_files": "PASS",
            "activation": activation,
        },
        "consumer_policy": {
            "framework_validation": "REUSE_INSTALL_RECEIPT",
            "product_validation": "REQUIRED",
            "framework_wide_scan": False,
        },
    }
    _write_atomic(receipt, value)
    return value


def check(
    root: Path, platform: str, receipt: Path, adapter_dst: Path, qa_dst: Path
) -> dict[str, object]:
    reasons: list[str] = []
    try:
        root = root.resolve(strict=True)
    except OSError:
        root = root.expanduser().absolute()
        reasons.append("installed_root_unreadable")
    try:
        value = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        value = {}
        reasons.append("receipt_missing_or_invalid")

    if not isinstance(value, dict):
        value = {}
        reasons.append("receipt_schema_invalid")

    if value.get("contract_version") != CONTRACT_VERSION:
        reasons.append("compatibility_changed")
    if value.get("status") != STATUS:
        reasons.append("receipt_not_verified")
    if value.get("installed_root") != str(root):
        reasons.append("installed_root_changed")
    if value.get("platform") != platform:
        reasons.append("platform_changed")

    try:
        current = _manifest(root, platform)
    except (OSError, TrustError):
        current = {}
        reasons.append("authority_set_unreadable")
    recorded = value.get("authority_manifest")
    if not isinstance(recorded, dict) or recorded != current:
        reasons.append("authority_drift")
    if current and value.get("compatibility_id") != _compatibility_id(current):
        reasons.append("compatibility_identity_mismatch")
    try:
        activation = _link_evidence(root, platform, adapter_dst, qa_dst)
    except (OSError, TrustError):
        activation = {}
        reasons.append("activation_invalid")
    recorded_validation = value.get("validation")
    recorded_activation = recorded_validation.get("activation") if isinstance(recorded_validation, dict) else None
    if activation and recorded_activation != activation:
        reasons.append("activation_evidence_mismatch")

    reasons = sorted(set(reasons))
    if reasons:
        return {
            "status": "REVALIDATE_REQUIRED",
            "reasons": reasons,
            "framework_validation": "INSTALL_OR_UPGRADE_ONLY",
            "product_validation": "REQUIRED",
        }
    return {
        "status": "TRUSTED",
        "installed_root": str(root),
        "platform": platform,
        "compatibility_id": value["compatibility_id"],
        "authority_files_checked": len(current),
        "framework_validation": "REUSED_INSTALL_RECEIPT",
        "product_validation": "REQUIRED",
        "framework_wide_scan": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("issue", "check"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--platform", required=True, choices=("codex", "cursor", "cline"))
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--adapter-dst", required=True, type=Path)
    parser.add_argument("--qa-dst", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = issue(
            args.root, args.platform, args.receipt, args.adapter_dst, args.qa_dst
        ) if args.action == "issue" else check(
            args.root, args.platform, args.receipt, args.adapter_dst, args.qa_dst
        )
    except TrustError as exc:
        result = {
            "status": "REVALIDATE_REQUIRED",
            "reasons": [str(exc)],
            "product_validation": "REQUIRED",
        }
    display = result
    if result.get("status") == STATUS:
        manifest = result.get("authority_manifest", {})
        display = {
            "status": STATUS,
            "installed_root": result["installed_root"],
            "platform": result["platform"],
            "compatibility_id": result["compatibility_id"],
            "authority_files_recorded": len(manifest) if isinstance(manifest, dict) else 0,
            "framework_wide_scan": False,
            "product_validation": "REQUIRED",
        }
    print(json.dumps(display, sort_keys=True))
    return 0 if result["status"] in {STATUS, "TRUSTED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())

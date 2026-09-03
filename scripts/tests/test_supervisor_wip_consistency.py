"""Guard the conditional supervisor-lane accounting across policy surfaces."""

from __future__ import annotations

import importlib.util
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def resolve_project_agents(root: Path) -> tuple[Path, Path]:
    """Use the consumer project's AGENTS.md, or the standalone root card."""

    project_root = root.parent
    project_agents = project_root / "AGENTS.md"
    if project_agents.is_file():
        return project_root, project_agents
    return root, root / "AGENTS.md"


WYSY_ROOT, PROJECT_AGENTS = resolve_project_agents(ROOT)
STANDALONE_LAYOUT = PROJECT_AGENTS == ROOT / "AGENTS.md"

SURFACES = (
    PROJECT_AGENTS,
    ROOT / "core" / "concurrency.md",
    ROOT / "core" / "orchestration.md",
    ROOT / "core" / "roles" / "lead.md",
    ROOT / "adapters" / "codex" / "SKILL.md",
    ROOT / "adapters" / "codex" / "runtime.md",
    ROOT / "README.md",
    ROOT / "core" / "README.md",
    ROOT / "core" / "qa-operating-model.md",
    ROOT / "docs" / "installation.md",
    ROOT / "docs" / "workflow.md",
    ROOT / "docs" / "adapters.md",
    ROOT / "docs" / "definitions.md",
    ROOT / "adapters" / "codex" / "agents" / "openai.yaml",
    ROOT / "adapters" / "cursor" / "SKILL.md",
    ROOT / "adapters" / "cursor" / "runtime.md",
    ROOT / "adapters" / "cline" / "SKILL.md",
    ROOT / "adapters" / "cline" / "runtime.md",
) + ((ROOT / "core" / "roles" / "monitor-agent.md",) if STANDALONE_LAYOUT else (ROOT / "AGENTS.md",))

QUALITY_SURFACES = (
    (PROJECT_AGENTS, re.compile(
        r"Code Reviewer.*?Test Engineer → Gatekeeper", re.DOTALL
    )),
    (ROOT / "core" / "concurrency.md", re.compile(
        r"Code Reviewer.*?Test Engineer when required → Gatekeeper", re.DOTALL
    )),
    (ROOT / "core" / "orchestration.md", re.compile(
        r"Code Reviewer → conditional Test Engineer → final Gatekeeper"
    )),
    (ROOT / "core" / "roles" / "lead.md", re.compile(
        r"Code Reviewer.*?Test Engineer.*?Gatekeeper", re.DOTALL
    )),
    (ROOT / "adapters" / "codex" / "SKILL.md", re.compile(
        r"Code Reviewer → conditional Test Engineer → Gatekeeper"
    )),
    (ROOT / "adapters" / "codex" / "runtime.md", re.compile(
        r"\| `code-reviewer`.*?\| `test-engineer`.*?\| `gatekeeper`",
        re.DOTALL,
    )),
    (ROOT / "README.md", re.compile(
        r"Code Reviewer → conditional Test Engineer → Gatekeeper"
    )),
    (ROOT / "core" / "README.md", re.compile(
        r"Code Reviewer → conditional Test Engineer → Gatekeeper"
    )),
    (ROOT / "core" / "qa-operating-model.md", re.compile(
        r"Code Reviewer → conditional TE → Gatekeeper"
    )),
    (ROOT / "docs" / "installation.md", re.compile(
        r"Code Reviewer → conditional Test Engineer\s*→ Gatekeeper"
    )),
    (ROOT / "docs" / "workflow.md", re.compile(
        r"Code Reviewer → conditional (?:Test Engineer|TE)\s*→ Gatekeeper"
    )),
    (ROOT / "docs" / "adapters.md", re.compile(
        r"Code Reviewer → conditional Test Engineer\s*→ Gatekeeper"
    )),
    (ROOT / "docs" / "definitions.md", re.compile(
        r"Code Reviewer.*?conditional Test Engineer.*?Gatekeeper", re.DOTALL
    )),
    (ROOT / "adapters" / "codex" / "agents" / "openai.yaml", re.compile(
        r"Code Reviewer → conditional Test Engineer → Gatekeeper"
    )),
    (ROOT / "adapters" / "cursor" / "SKILL.md", re.compile(
        r"Code Reviewer → conditional Test Engineer → Gatekeeper"
    )),
    (ROOT / "adapters" / "cursor" / "runtime.md", re.compile(
        r"Code Reviewer → conditional Test Engineer → Gatekeeper"
    )),
    (ROOT / "adapters" / "cline" / "SKILL.md", re.compile(
        r"Code Reviewer → conditional Test\s+Engineer → Gatekeeper"
    )),
    (ROOT / "adapters" / "cline" / "runtime.md", re.compile(
        r"Code Reviewer → conditional Test Engineer → Gatekeeper"
    )),
) + ((
    (ROOT / "core" / "roles" / "monitor-agent.md", re.compile(
        r"Replace Code Reviewer, Test Engineer, Gatekeeper"
    )),
) if STANDALONE_LAYOUT else (
    (ROOT / "AGENTS.md", re.compile(
        r"Code Reviewer → conditional Test Engineer → Gatekeeper"
    )),
))

TYPED_WIP_MARKERS = (
    "ordinary",
    "supervisor",
    "3",
)

ORDINARY_WIP_PATTERN = re.compile(
    r"(?:WIP\s*(?:≤|<=)\s*2|≤\s*2|ordinary.{0,100}\b2\b)",
    re.IGNORECASE,
)


def validate_required_surfaces(surfaces: tuple[Path, ...]) -> None:
    """Fail closed when required policy files are missing or duplicated."""

    if len(surfaces) != len(set(surfaces)):
        raise AssertionError("required policy surfaces must be unique")
    missing = [path for path in surfaces if not path.is_file()]
    if missing:
        raise AssertionError(
            "missing required policy surfaces: "
            + ", ".join(str(path) for path in missing)
        )

DISPATCH_SCRIPT = (
    ROOT / "adapters" / "codex" / "scripts" / "prepare-dispatch.py"
)
DISPATCH_SPEC = importlib.util.spec_from_file_location(
    "supervisor_wip_prepare_dispatch", DISPATCH_SCRIPT
)
if DISPATCH_SPEC is None or DISPATCH_SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"cannot load {DISPATCH_SCRIPT}")
PREPARE_DISPATCH = importlib.util.module_from_spec(DISPATCH_SPEC)
DISPATCH_SPEC.loader.exec_module(PREPARE_DISPATCH)

class SupervisorWipConsistencyTests(unittest.TestCase):
    def test_required_surfaces_keep_typed_conditional_lane_limit(self) -> None:
        self.assertEqual(len(SURFACES), 19)
        validate_required_surfaces(SURFACES)
        for path in SURFACES:
            with self.subTest(path=path.relative_to(WYSY_ROOT)):
                text = path.read_text(encoding="utf-8")
                for marker in TYPED_WIP_MARKERS:
                    self.assertIn(marker, text)
                self.assertRegex(text, ORDINARY_WIP_PATTERN)

    def test_required_surfaces_preserve_reviewer_te_gatekeeper_order(self) -> None:
        self.assertEqual(len(QUALITY_SURFACES), 19)
        validate_required_surfaces(tuple(path for path, _ in QUALITY_SURFACES))
        for path, pattern in QUALITY_SURFACES:
            with self.subTest(path=path.relative_to(WYSY_ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertRegex(text, pattern)

    def test_standalone_layout_resolves_its_own_agents_card(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            base = Path(temporary_root)
            standalone = base / "standalone"
            standalone.mkdir()
            standalone_agents = standalone / "AGENTS.md"
            standalone_agents.write_text("standalone", encoding="utf-8")
            self.assertEqual(
                resolve_project_agents(standalone),
                (standalone, standalone_agents),
            )

            consumer = base / "consumer"
            checkout = consumer / "coding-team"
            checkout.mkdir(parents=True)
            consumer_agents = consumer / "AGENTS.md"
            consumer_agents.write_text("consumer", encoding="utf-8")
            checkout_agents = checkout / "AGENTS.md"
            checkout_agents.write_text("checkout", encoding="utf-8")
            self.assertEqual(
                resolve_project_agents(checkout),
                (consumer, consumer_agents),
            )

    def test_missing_required_surface_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            present = Path(temporary_root) / "present.md"
            present.write_text("policy", encoding="utf-8")
            missing = Path(temporary_root) / "missing.md"
            with self.assertRaisesRegex(AssertionError, "missing required"):
                validate_required_surfaces((present, missing))
            with self.assertRaisesRegex(AssertionError, "must be unique"):
                validate_required_surfaces((present, present))

    def test_concurrency_forbids_authoritative_or_recursive_supervision(self) -> None:
        text = (ROOT / "core" / "concurrency.md").read_text(encoding="utf-8")
        self.assertIn("non-authoritative observation only", text)
        self.assertIn("must not mutate", text)
        self.assertIn("supervise another supervisor", text)
        self.assertIn("No supervisor lane means no extra slot", text)

    def test_monitor_agent_role_card_is_registered_and_dispatchable(self) -> None:
        card = ROOT / "core" / "roles" / "monitor-agent.md"
        self.assertTrue(card.is_file())
        card_text = card.read_text(encoding="utf-8")
        self.assertIn("read-only supervisor relay", card_text)
        self.assertIn("One create-once relay result", card_text)
        self.assertIn(
            "Spawn or manage roles, issue follow-up tasks or messages, or control sibling execution",
            card_text,
        )
        self.assertIn("never controls work or accepts", ROOT.joinpath("docs/definitions.md").read_text(encoding="utf-8"))
        self.assertIn("monitor-agent", PREPARE_DISPATCH.CANONICAL_ROLES)
        self.assertEqual(PREPARE_DISPATCH.HOST_AGENT_TYPES["monitor-agent"], "explorer")

        result = PREPARE_DISPATCH.prepare_dispatch(
            {
                "role": "monitor-agent",
                "task_id": "CT-SUPERVISOR-REACHABILITY",
                "objective": "Relay one bounded PIC attempt's artifact state to Lead.",
                "acceptance": [
                    "Publish at most one create-once relay result without host authority.",
                ],
                "paths": [
                    "implementation/architecture-contracts/coding-team-supervisor-relay-v1.md",
                    "private/runtime/supervisor-relay/reservation.json",
                ],
                "validation": [
                    "python3 -m pytest adapters/codex/tests/test_supervisor_relay.py -q",
                ],
                "stop": "Stop on reservation drift, mutation need, or a second supervisor lane.",
                "model": "gpt-5.6-luna",
                "effort": "medium",
                "fork_context": False,
                "allocation": {
                    "owner": "monitor-agent",
                    "concern": "one supervisor relay observation",
                    "input_refs": [
                        "implementation/architecture-contracts/coding-team-supervisor-relay-v1.md",
                        "private/runtime/supervisor-relay/reservation.json",
                    ],
                    "result": "one bounded dispatch decision",
                    "prerequisites": [
                        {"name": "reservation is readable", "status": "passed"},
                    ],
                    "candidate_changed_paths": 2,
                    "prior_hard_stop": False,
                    "timing_profile": {
                        "target_s": 10,
                        "checkpoint_s": 20,
                        "hard_stop_s": 30,
                        "reserve_s": 5,
                        "max_hard_cap_s": 30,
                    },
                    "priced_units": {
                        name: [{
                            "status": "MEASURED",
                            "seconds": 1,
                            "source": "test fixture",
                            "evidence_ref": "receipt:test-duration",
                        }]
                        for name in ("setup", "work", "validation", "handoff")
                    },
                },
            },
            ROOT,
        )
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["role"], "monitor-agent")
        self.assertEqual(result["spawn"]["agent_type"], "explorer")
        self.assertEqual(Path(result["role_card"]), card.resolve())


if __name__ == "__main__":
    unittest.main()

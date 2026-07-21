# Codex runtime — role delegation

Lead (this skill) classifies nature, writes a ≤250-word run prompt, and spawns **one** Codex subagent per task. Prefer independent subagents with the mapped model/effort from `model-pool.map.md`.

## Delegation table

| Canonical role | When to spawn | Codex pattern | Tier (look up map) | Notes |
|---|---|---|---|---|
| `investigator` | N0 map/fact; N2/N5 pre-scan | Subagent, read-mostly | 0 (1 if cross-file) | Path/line evidence only; no edits |
| `advisor` | N2/N4/N5 direction | Subagent, read-only | 2 | Pre-build verdict; never implements or Gatekeeps |
| `contradictor` | Required N2/N4/N5 debate | Subagent, read-only | 2 | **Serial after Advisor**; never parallel with Advisor under WIP |
| `product-manager` | Ambiguous product scope | Subagent | 2 | Consult peer; not under Advisor |
| `backend-engineer` | Server/API/persistence | Subagent, write to owned paths | 1 build | Exclusive file ownership |
| `frontend-builder` | UI implement after UX contract | Subagent, write to owned paths | 1 build | No product/UX direction ownership |
| `frontend-ux-lead` | Journey/UX contract | Subagent | 1–2 | Contract first; implement only if brief assigns writes |
| `docs-steward` | Named durable docs | Subagent | 0 | After accepted validation when gate requires docs |
| `test-engineer` | Batch V0–V3 evidence | Subagent | 1 validate | Before Gatekeeper only |
| `gatekeeper` | Post-TE accept/block | Subagent, read-only | 2 | **After** fresh TE evidence; never with TE |
| Lead (parent) | Orchestrate only | This skill / main thread | 2 for plan; else ambient | No implementation code from Lead |

## Sequencing rules

```text
WIP ≤ 2 tool-using subagents at once
Debate (when required): Investigator → Advisor → Contradictor → Lead resolve → build → TE → GK
Validation gate: Test Engineer completes → then Gatekeeper
Incomplete / non-APPROVE → stop → ask human
```

## Prompt packet (every spawn)

Pass only: objective, acceptance, exclusive write/read paths, evidence pointers, validation command, stop condition, mapped `model` + `effort` if the runtime supports them. Do not paste full files, diffs, or prior transcripts.

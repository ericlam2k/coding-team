# Runtime evidence — validation report (to main / verification)

**Validates:** `adapters/opencode/eval/runtime-evidence-request.md` (status `EVIDENCE_REQUESTED`)
**Prepared by:** opencode adapter (Lead)
**Date:** 2026-08-21
**Recorded SHA:** `69a3b13947cd3b3ef9b6a740f8ece1ec2dad59c0`
**Scope:** private lab adapter only; no implementation or release decision.

---

## 1. Validation verdict

The request is **well-formed and aligned** with the framework and the as-built
plugin. **No blocking defects in the plugin.** Framework-reload runtime evidence
is now `MEASURED` (live `DEBUG=1` run on 2026-08-21). Two items remain for main's
attention: (1) terminology clarification, (2) the model-fallback fail-event gap.

1. **Terminology clarification** — the request's "Fallback" section means
   *model* fallback (`opencode-model-fallback`), which is a **separate,
   pre-existing** plugin. It is distinct from `framework-reload`'s re-anchor,
   which the earlier maintree audit loosely called a "fallback." Main should not
   conflate them.
2. **Fresh live run delivered (framework-reload).** After the audit fix
    (`69a3b13`) default mode writes **no host log**, but a `DEBUG=1` run on
    2026-08-21 (02:35–02:37) produced `~/.config/opencode/framework-reload-plugin.log`
    capturing: plugin **loaded ×3**, `experimental.session.compacting` **received**
    (pending=1), and `re-anchored framework` after **both** the first `/compact`
    and a re-compaction. `SCN-LOAD`, `SCN-COMPACT`, `SCN-RECOMPACT`, and
    `SCN-FS-DEBUG` are now **MEASURED**. Per the request's rule ("do not infer
    live activation from source or a simulated test"), these come from an
    authoritative host receipt, not from `test-activation.mjs`.
3. **Live model-fallback observation (partial, unchanged).** A live
    `~/.config/opencode/fallback-plugin.log` shows `opencode-model-fallback` is
    **loaded and operational** in the host (logs per-agent primary/fallback
    chains + `CHAT` entries). But during the observed window **no actual fallback
    event occurred** (`fallback=false` throughout), and the `WARN` "No agents
    configured in `~/.config/opencode/fallback-models.json`" persists — the
    plugin reads a **global** config path, not the repo's `model-fallback.json`.
    The fail→fallback scenario (`SCN-FALLBACK`) therefore remains `UNAVAILABLE`;
    `SCN-FALLBACK-LOAD` is `MEASURED` (plugin live).

---

## 2. Alignment checks (request clause → as-built reality)

| Request clause | As-built reality | Status |
|---|---|---|
| Plugin-load evidence | `opencode.json` uses repo-relative `../adapters/opencode/framework-reload/index.js` (audit fix #3); live `DEBUG=1` run shows `plugin loaded` ×3 → load receipt **MEASURED** | ✅ live receipt |
| Compaction lifecycle: inject-once, no dup late | `index.js` enforces `pending`+`done` dedupe; `test-activation.mjs` asserts | ✅ logic proven |
| Re-compaction: 1 re-anchor/cycle, stable id | `done.delete(sessionID)` on `experimental.session.compacting` | ✅ logic proven |
| Edge: empty/non-string system, 65 pending, missing id, malformed payload | Guards: `typeof sessionID==="string"`, `Array.isArray(output.system)`, `typeof output.system[0]==="string"`; `MAX_PENDING=64` → eviction at 65th | ✅ logic proven (executed in `test-activation.mjs`) |
| Fallback (model) | `opencode-model-fallback` — separate plugin; **live activation never triggered in lab** | ⚠️ terminology + genuinely unproven |
| Filesystem effects (default vs debug, direct vs host logger) | Writes gated behind `FRAMEWORK_RELOAD_DEBUG`; default = no plugin writes (audit fix #2) | ✅ aligns |
| Report shape + `MEASURED/UNAVAILABLE/BLOCKED` + redaction | Consistent with `core` QA-evidence model and `adapters/opencode/AGENTS.md` Trial Scope | ✅ |
| Acceptance boundary (lab only) | Matches AGENTS.md "no push to origin / no public sync without separate human approval" | ✅ |

---

## 3. Draft report rows (current status)

Columns per the request: `scenario_id`, `host_version`, `planned_model`,
`actual_model`, `event_received`, `injection_count`, `fallback_reason`,
`receipt_path`, `filesystem_delta`, `status`, `notes`.

| scenario_id | host_version | planned_model | actual_model | event_received | injection_count | fallback_reason | receipt_path | filesystem_delta | status | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| SCN-LOAD | opencode (live, 2026-08-21T02:36) | — | — | yes (`plugin loaded` ×3) | — | — | `~/.config/opencode/framework-reload-plugin.log` | n/a | MEASURED (live) | Repo-relative path confirmed loaded in host |
| SCN-COMPACT | opencode (live, 02:36:24) | — | — | `experimental.session.compacting` | 1 | — | `~/.config/opencode/framework-reload-plugin.log` | n/a | MEASURED (live) | `marked compacted` (pending=1) → `re-anchored framework` |
| SCN-RECOMPACT | opencode (live, 02:37:52) | — | — | `experimental.session.compacting` | 1/cycle | — | `~/.config/opencode/framework-reload-plugin.log` | n/a | MEASURED (live) | Second `/compact` → 2nd `re-anchored framework` (re-anchor on genuine re-compaction) |
| SCN-EDGE-65 | UNAVAILABLE | — | — | UNAVAILABLE (sim) | evict@64 (sim) | — | BLOCKED | — | 65th session triggers FIFO eviction — not exercised live; proven in `test-activation.mjs` |
| SCN-FALLBACK-LOAD | live host | — | — | yes (plugin active) | — | — | `~/.config/opencode/fallback-plugin.log` | n/a | MEASURED (live) | Plugin loaded **and primary-override routing proven**: `investigator` was routed to a *custom* primary `Nemotron Ultra 3 Free` (4 live calls, all succeeded) — a primary the host would never pick by default. Fallback chain armed (`hy3 → glm-5.3 → deepseek-v4-flash`). |
| SCN-FALLBACK | UNAVAILABLE | — | — | UNAVAILABLE | — | unproven (no `fallback=true` observed) | BLOCKED | — | `opencode-model-fallback` live; primary-override routing **proven for 5 custom primaries** (`Nemotron Ultra 3 Free`, `opencode-zen/claude-opus-5`, `nemotron nano`, `Claude-Fable-5`, `gpt image`) — all routed correctly. Fallback chain armed; error-detection active (`Not a quota/rate-limit error, ignoring`). Fail→fallback event NOT reproduced: **every** attempted primary succeeded (`fallback=false`), incl. 3 slugs absent from the pool (`nemotron nano`, `Claude-Fable-5`, `gpt image`) — the host serves unknown slugs rather than erroring. No primary emitted a fallback-eligible error (rate_limit/5xx/overload/quota/timeout) in this env → `fallback=true` never emitted. |
| SCN-FS-DEFAULT | n/a | n/a | n/a | n/a | 0 writes | n/a | `test-activation.mjs` + live default compact | no log file created | MEASURED (sim) / live-consistent | Simulated; live default compact also produced no framework-reload log (expected) |
| SCN-FS-DEBUG | opencode (live, 02:35–02:37) | n/a | n/a | n/a | writes iff `DEBUG=1` | n/a | `~/.config/opencode/framework-reload-plugin.log` (739 B, 7 lines) | created log file | MEASURED (live) | `FRAMEWORK_RELOAD_DEBUG=1` → diagnostic host log emitted; confirms env-gated filesystem delta |

`test-activation.mjs` result this session: **PASS** (inject-once, no
double-inject from late `session.compacted`, re-anchor on re-compaction, no log
file in default mode). This is **logic** proof only and, per the request, cannot
substitute for an authoritative OpenCode receipt.

---

## 4. Clarifications / risks for main

- **"Fallback" = model fallback**, not `framework-reload`'s re-anchor. The two
  audit threads used "fallback" differently; this request's Fallback section is
  about `opencode-model-fallback`.
- **Post-fix obsolescence — RESOLVED for framework-reload:** default mode still
   writes no host log, but the `DEBUG=1` run now provides an authoritative host
   receipt (load ×3, re-anchor after compact + re-compaction). `SCN-*` for
   framework-reload are `MEASURED`. The model-fallback *fail event* remains
   unproven (see below).
- **Simulated ≠ live:** `test-activation.mjs` validates the hook *logic* and is
   still the proof for `SCN-EDGE-65`; it does not substitute for the live
   framework-reload receipt (now captured) or a model-fallback fail event.
- **Config-path mismatch (model-fallback) — STILL PENDING:** live
   `fallback-plugin.log` still warns "No agents configured in
   `~/.config/opencode/fallback-models.json`" (last at 02:36:20). The plugin
   reads a **global** path, not the repo's `adapters/opencode/model-fallback.json`.
   For a clean fail→fallback test, configure the *primary* (to a failing model)
   in that **global** file; otherwise the run cannot exercise the intended chain.

---

## 5. Recommendation

Accept `runtime-evidence-request.md` as the verification contract. **Run 1
(framework-reload) is complete:** a `DEBUG=1` restart with the repo-relative
config produced `SCN-LOAD`, `SCN-COMPACT`, `SCN-RECOMPACT`, and `SCN-FS-DEBUG` as
`MEASURED`. **Run 2 (model-fallback fail event) is still `BLOCKED`:** configure a
*failing primary* in the **global** `~/.config/opencode/fallback-models.json`,
send a prompt, and confirm a `fallback=true` line in `~/.config/opencode/fallback-plugin.log`
to move `SCN-FALLBACK` → `MEASURED`. Keep strictly within lab scope — no
commit/push/release. If an authoritative receipt cannot be produced, report
`BLOCKED`, exactly as the request's Acceptance boundary states.

---

## 6. Compliance

- `core/` untouched; opencode adapter only. ✅
- Acceptance boundary respected (lab validation only). ✅
- Redaction guidance noted (no secrets / raw prompts / private paths / tokens). ✅
- Evidence recorded at a recorded SHA (`69a3b13…`). ✅

---

## 7. Re-validation 2026-08-26 (hermetic-test correction; model-fallback status check)

Candidate tree `32fd14f0073eecf05fc0ff2d1fc2cdcecb74fac6` (dirty working tree,
uncommitted; lab-only). No `core/` or runtime-plugin changes.

1. **framework-reload test made hermetic (test-only correction).** The earlier
   failure (`default mode must not write a host log file / actual true`) was
   reproduced-classified as **test-environment contamination**: the old test
   deleted the real user host log before asserting its absence, so any
   pre-existing undeletable log failed assertion 5 spuriously.
   `test-activation.mjs` now runs against an isolated temp HOME set before
   importing `index.js`, never touches the user log, asserts default mode
   creates no new log, and adds an explicit pre-existing-log independence
   proof (sentinel file left byte-identical). Re-run results: normal →
   **PASS (exit 0)**; contaminated-HOME scenario → **PASS**, sentinel
   byte-identical; negative control `FRAMEWORK_RELOAD_DEBUG=1` → **fails exit 1**
   (guard detects real writes). `SCN-FS-DEFAULT` semantics unchanged.
2. **Model-fallback practice record (zen-pool trial, `d1bce28`) validated
   current as of 2026-08-26.** Live `~/.config/opencode/fallback-plugin.log`
   (entries through 2026-08-26T02:14Z) still contains **zero** `fallback=true`
   lines → `SCN-FALLBACK` remains **BLOCKED** (fail→fallback event unproven;
   every attempted primary keeps succeeding). Section 4's pending items stand:
   configure a *failing primary* in the **global**
   `~/.config/opencode/fallback-models.json` to exercise the intended chain.

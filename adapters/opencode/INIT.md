# OpenCode init prompt (copy-paste)

Paste the block below into OpenCode as the first message of a session opened in
this repo (`/Users/quanglam/Documents/Wysy/coding-team`). Replace `<TASK>` with
your coding task. No other setup is required.

```text
You are the Lead of coding-team for this repo. Working directory:
/Users/quanglam/Documents/Wysy/coding-team

1. Set CODING_TEAM_ROOT=/Users/quanglam/Documents/Wysy/coding-team.
2. Read adapters/opencode/AGENTS.md, adapters/opencode/runtime.md, and
   $CODING_TEAM_ROOT/core/orchestration.md. Load role cards from core/roles/ as needed.
3. Confirm trial scope: lab-only branch adapter/opencode-wysy-lab; reuse core/
   read-only; no core/ changes; no push/merge to main; no public sync.
4. Use the approved adapters/opencode/model-pool.map.md when it is marked
   approved; otherwise treat tiers as non-binding.
5. Work rules: WIP <= 2, disjoint writes, Code Reviewer -> QA route ->
   Gatekeeper under core/qa-operating-model.md, human approval before irreversible actions, and record for every
   run: actual model IDs, exit state, artifacts, and the commit SHA.
6. Now start this task: <TASK>
```

## Optional session add-ons

- Approve the OpenCode model map (from OpenCode or a shell):
  `./bin/ct map approve --platform opencode` (tiers are non-binding until then).
- Learning / experiment / distillation are WYSY-owned (see the WYSY repo
  `AGENTS.md` and `scripts/learning-framework.py`); if you need them this
  session, open OpenCode in `/Users/quanglam/Documents/Wysy`.

## After the session

```bash
git switch main   # return the checkout to the Codex runtime branch
```

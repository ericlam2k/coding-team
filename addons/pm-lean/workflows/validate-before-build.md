# Validate before build

Documentation-only recipe. Each arrow is a separate Product Manager task and a named human stop; it never auto-chains, invokes roles/models/tools, or changes batch state.

```text
$pm-lean-assumption-triage
→ Human: select one assumption or stop
→ $pm-lean-experiment-design
→ Human: review evidence and decide validate, revise, or stop
→ existing skills/process/pm-execution/wwas/
→ Human: admit or decline the resulting brief
→ Lead applies normal Coding Team routing
```

For a production, destructive, or user-impacting experiment, the second human stop is mandatory before any canonical workflow can act.

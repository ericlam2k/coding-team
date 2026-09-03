# GPT-5.6 optional prompt overlays

This adapter-local pack contains optional prompt overlays. The fixed Coding
Team core is the sole authority for nature classification, canonical roles,
tiers, model selection, skills, sequencing, concurrency, and gates. The Lead
first completes core routing and resolves the actual model through
`model-pool.map.md`; only then may it load a matching profile overlay and at
most one compatible workflow from `skills/manifest.json` into that same call.

The pack starts unloaded and adds zero model calls. It has no router, runtime
availability map, fallback model logic, automatic profile selection, automatic
stage, or automatic Guard call. Sol, Terra, and Luna overlays follow the actual
model already selected by core; they never cause a model switch. Guard is only
an in-call checklist applied by the already selected canonical owner. It emits
no independent verdict and never replaces Advisor, Contradictor, Test Engineer,
Gatekeeper, host policy, or a human stop.

Available optional workflows:

- `prompt-audit`
- `prompt-compression`
- `safety-policy-extraction`

One workflow maximum; the Lead selects it only after core role/nature/tier/model
routing. WIP <= 2, Advisor -> Contradictor serial when required, builders ->
Test Engineer -> Gatekeeper, and all human gates remain unchanged.

```sh
node scripts/validate.mjs
```

This directory is not wired into the runtime and makes no availability,
fallback, performance, or measured-benefit claim. Lower prompt cost and clearer
task focus are expected benefits only and require independent measurement.

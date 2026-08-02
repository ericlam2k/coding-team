---
name: stakeholder-update
description: Draft a concise leadership, project-status, or incident update from supplied verified Sprint, Batch, checkpoint, Test Engineer, and Gatekeeper evidence. Use only when explicitly invoked by the Docs Steward; do not use for research, orchestration, acceptance, or implementation.
---

# Stakeholder update

Use only in the existing Docs Steward turn. Do not research, call tools or models, open work, change routing, or create acceptance evidence. Use only supplied verified Sprint, Batch, checkpoint, Test Engineer, and Gatekeeper material.

1. Separate direct evidence from inference. Label inference and do not turn it into fact.
2. Stop and name the conflicting sources when material sources disagree; do not reconcile them by assumption.
3. Omit secrets, credentials, private customer data, and unnecessary identifiers.
4. Never claim completion beyond the recorded Test Engineer and Gatekeeper outcomes.

Return at most 200 words in this format:

```text
Progress
- Evidence: ...
- Inference: ... (only when needed)

Plans
- Evidence: ...

Problems/Risks
- Evidence: ...

Decision needed
- None
```

Replace `None` with a specific owner and decision when evidence requires one. Keep each field factual and concise.

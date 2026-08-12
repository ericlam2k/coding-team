# Next-sprint backlog

This list is proposed work. None of these items are shipped by the public
candidate unless the repository later gains the implementation, tests, and
documentation to support the claim.

## Communication adaptation

- **User-selected mode in a host adapter** — expose a small, explicit setting
  for `familiar analogy` or `direct technical`, with a clear default and a
  visible way to change it.
- **Background-aware onboarding, only with consent** — ask what explanation
  style helps the user. Do not infer a communication style from occupation,
  identity, or demographic data.
- **Preference persistence** — decide whether a host should remember the
  choice, where it is stored, and how the user clears or overrides it.
- **Runtime translation layer** — render the same contract in approachable
  language while preserving exact terms, statuses, evidence, and stop rules.

## Language and content

- **EN / VI / CN editions** — translate the source material with terminology
  review and a checked glossary. The Chinese edition may use the approved
  DeepSeek Flash workflow when that model is available and explicitly
  approved; model availability is not a release claim.
- **Marketing and social review** — invite a copywriter or domain advisor for
  a separate review of positioning, Facebook/X drafts, and product-safe claims.
- **Demonstration visuals** — create a small, accessible visual case study
  after the scenario and message are stable. Label illustrative visuals as
  examples, not execution evidence.

## Acceptance questions for implementation

Before this backlog moves into a sprint, answer:

1. Is the setting conversation-only, host-level, or persisted?
2. What exact output stays invariant across communication modes?
3. How will a user override adaptation and inspect the active mode?
4. What tests prove that a metaphor never changes `PASS`, `FAIL`, `BLOCKED`,
   evidence, or human-gate behavior?

Use the existing Sprint → Batch → Task process to turn each accepted answer
into a bounded task. Do not advertise a proposed item as a current feature.

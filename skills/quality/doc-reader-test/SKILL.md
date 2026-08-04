---
name: doc-reader-test
description: Validate a major ADR, RFC, architecture, public-contract, security, or compliance document by testing whether a fresh reader can make its intended decision from the document alone. Use only when explicitly invoked for a named major document with its intended audience and decision; do not use for minor documentation, routine README changes, or general editing.
---

# Document Reader Test

Run one fresh-context Test Engineer review of one major document. Judge only whether the named audience can make the named decision from that document.

## Required Input

Accept only:

- the named document
- the intended audience
- the decision the document must support

Stop and request a missing item. Do not fill gaps from conversation history, repository knowledge, external sources, or assumptions.

## Reader Test

1. Read the document once as the intended audience.
2. Generate three to five realistic questions that reader must resolve to make the intended decision. Favor scope, constraints, tradeoffs, interfaces, risks, ownership, rollout, or verification when relevant.
3. Answer each question only from the document. Cite the relevant heading, section, or brief excerpt location.
4. Mark each answer as one of:
   - `Answered` — the document supplies a clear, decision-usable answer.
   - `Unanswered` — the required answer is absent.
   - `Ambiguous` — multiple reasonable interpretations remain.
   - `Contradictory` — document statements materially conflict.
   - `Assumed knowledge` — the answer depends on unexplained context or terminology.
5. Return `PASS` only when every decision-critical question is answered and no material ambiguity, contradiction, or assumed knowledge blocks the intended decision. Otherwise return `REVISE`.

## Output

```text
Reader: <intended audience>
Decision: <intended decision>

1. Question: ...
   Answer: ...
   Evidence: <document location>
   Finding: <Answered | Unanswered | Ambiguous | Contradictory | Assumed knowledge>

Verdict: <PASS | REVISE>
Evidence: <concise verdict basis>
Fixes: <smallest document changes needed, or None>
```

Keep the result concise. Scope `PASS` to reader sufficiency only; it is not product completion, test completion, approval, or Gatekeeper acceptance.

## Boundaries

- Use one fresh Test Engineer call for the complete test. Do not create a subagent per question.
- Do not rewrite or edit the document.
- Do not research externally, open unrelated files, or invent facts.
- Do not implement, approve, route, orchestrate, or act as Gatekeeper.
- Do not claim product completion, test-suite completion, release readiness, or policy compliance.

# DESIGN.md reference index

`awesome-design-md` is a **named-lookup reference library**, not project design authority and not a substitute for Hallmark.

## Authority order

1. Human-approved project artwork, brand guidelines, and governing specs
2. Existing project tokens / CSS / design system
3. Explicitly named `awesome-design-md/design-md/<brand>/DESIGN.md` for **principle extraction only**
4. Generated recommendations from `ui-ux-pro-max` / `frontend-design` (last)

When Hallmark is assigned, it outranks `frontend-design` / `aesthetic` / `ui-ux-pro-max` unless the brief names a narrower trigger.

## Usage rules

- Read this index first; do **not** browse the full catalog or paste multiple `DESIGN.md` bodies into a prompt.
- When assigned: Read at most **one primary** and **one comparison** `DESIGN.md`.
- Extract principles only (hierarchy, density, spacing rhythm, accent discipline, reading measure). Do **not** clone branding, proprietary fonts, logos, copy, or product-specific patterns.
- Do **not** copy a third-party `DESIGN.md` into the project root as authority.
- Prefer `DESIGN.md` over `preview.html` unless the task explicitly needs a visual swatch check.
- Express accepted choices through project-owned tokens/CSS after human or UX-contract acceptance.

Path pattern:

```text
skills/design/awesome-design-md/design-md/<folder>/DESIGN.md
```

Upstream catalog README: `skills/design/awesome-design-md/README.md`.

## Useful named lookups (assign explicitly)

| Intent | Folder |
|---|---|
| Warm workspace / approachable modules | `notion` |
| Precise product-craft / sparse accent | `linear.app` |
| Reading-first docs measure | `mintlify` |
| Black/white deployment precision | `vercel` |
| Payment / trust gradients (fintech reference only) | `stripe` |
| Docs / headless CMS editorial | `sanity` |
| Scheduling / calm SaaS | `cal` |
| Messaging / conversational UI | `intercom` |
| Design-tool vibrancy (sparingly) | `figma` |
| Motion-forward marketing | `framer` |
| Warm retail / marketplace photography | `airbnb` |
| Enterprise structure | `ibm` |

If the task names a brand not listed, resolve `design-md/<folder>/DESIGN.md` by exact folder name; if missing, stop and ask Lead — do not invent a substitute.

## Role routing

- **Frontend/UX Lead:** owns which named reference(s) apply; cites path(s) in the UX contract.
- **Frontend Builder:** reads only paths named in the UX contract or task brief.
- **Investigator:** may locate a named path when assigned; never chooses visual direction.
- **Gatekeeper:** may check that implementation did not copy third-party identity; does not browse for taste.

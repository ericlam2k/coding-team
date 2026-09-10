# DESIGN.md reference index

`awesome-design-md` is a **named-lookup reference library**, not project design authority and not a substitute for Hallmark.

Start with [`design-router.md`](design-router.md) for the surface scenario.
The router selects exactly one primary generator; this index only governs
named `DESIGN.md` principle references.

## Authority order

1. Human-approved project artwork, brand guidelines, and governing specs
2. Existing project tokens / CSS / design system
3. The admitted UX contract and its router-selected primary generator
4. Exactly one named `awesome-design-md/design-md/<brand>/DESIGN.md` for
   **principle extraction only** on the `brand_web` route

## Usage rules

- Read this index first; do **not** browse the full catalog or paste multiple `DESIGN.md` bodies into a prompt.
- On `brand_web`: read exactly **one** contract-named `DESIGN.md`.
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

- **Frontend/UX Lead:** selects the route and one named reference for
  `brand_web`; cites its exact path in the UX contract.
- **Frontend Builder:** reads only the primary generator and route resources named in the UX contract or task brief.
- **Investigator:** may locate a named path when assigned; never chooses visual direction.
- **Gatekeeper:** may check that implementation did not copy third-party identity; does not browse for taste.

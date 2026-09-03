# Scenario design router

This host-neutral router chooses one primary design generator for a surface.
It is a routing contract, not a second design system. Product requirements,
the existing product system, and the admitted UX contract outrank every route.

## Route contract

Every route result contains:

- `scenario`: one of the explicit scenarios below
- `primary_generator`: exactly one named skill
- `route_resources`: only the files the UX contract names for the Builder
- `finish_lens`: `skills/design/aesthetic/`
- `finish_lens_authority`: `non-authoritative`
- `rendered_visual_inspection`: required before a completion claim

The aesthetic skill is always a finish lens. It can identify visual defects
and suggest craft improvements, but it cannot change product requirements,
accessibility, the UX contract, or the selected primary generator.

## Routes

| Surface scenario | Primary generator | Named route resources | Use when |
|---|---|---|---|
| `operational` | `skills/design/anti-ui-slop/` | `reference/operate.md` | Dashboards, admin, workbenches, planners, and other task-focused product UI |
| `brand_web` | `skills/design/hallmark/` | Exactly one named `awesome-design-md/design-md/<brand>/DESIGN.md`, selected through `skills/design/design-md-index.md` | Landing, marketing, or brand presentation surfaces |
| `expressive` | `skills/design/frontend-design/` | Only the contract-named frontend-design references | Art-directed experiences where expression is the product outcome |
| `refinement` | `skills/design/anti-ui-slop/` | `reference/polish.md` | Improving an existing interface without changing its product direction |
| `usability_audit` | `skills/design/anti-ui-slop/` | `reference/audit.md` | An explicit usability or anti-slop audit |

Choose one route per surface, not one route per product. A product may use
several routes while shared tokens, components, terminology, status semantics,
accessibility rules, and interaction grammar remain consistent.

## Anti-ui-slop playbook limit

Load at most one file from `skills/design/anti-ui-slop/reference/` for a task.
The route determines that file. Do not combine `new-work.md`, `operate.md`,
`polish.md`, `distill.md`, `audit.md`, or `ios.md` in one task. The anti-ui-slop
skill itself remains unchanged from its pinned upstream source.

`awesome-design-md` is a named principle reference for the `brand_web` route,
not a second primary generator. Read the index first and load exactly one
named `DESIGN.md` when the UX contract explicitly names it.

Hallmark and `frontend-design` are mutually exclusive primary generators for
one task. If the route is `brand_web`, Hallmark generates; if it is
`expressive`, `frontend-design` generates. Neither is loaded as a second
generator for the same task.

## Ownership and handoff

The Frontend UX Lead selects the route and owns the UX contract. The contract
records the scenario, primary generator, named resources, required states,
responsive constraints, accessibility expectations, and visual-inspection
evidence. The Frontend Builder consumes only that contract and its named route
resources; it does not select a generator or browse additional design skills.

The contract must not claim completion until the rendered surface has been
inspected at representative widths and relevant states. A source-only or
markup-only check is not rendered visual inspection.

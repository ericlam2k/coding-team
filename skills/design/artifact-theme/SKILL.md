---
name: artifact-theme
description: Apply a restrained, accessible visual theme to non-product artifacts such as slide decks, reports, PDF or document covers, and static stakeholder materials. Use only when the user explicitly invokes $artifact-theme; never use it to govern websites, Next.js applications, product UI, or design systems.
---

# Artifact Theme

Style a non-product artifact without introducing a new design system, dependency, asset, or workflow authority.

## Apply the Theme

1. Inspect the artifact and its surrounding project for `DESIGN.md`, brand guidelines, templates, logos, established colors, or typography.
2. Treat existing brand guidance and assets as authoritative. Reuse them and describe the result as `Project brand`; do not blend in a preset unless the user requests it.
3. When no brand exists, read [references/themes.md](references/themes.md) and select the theme that best fits the artifact's audience and purpose. Default to `Ledger Blue` when evidence does not favor another theme. Do not interrupt the user to ask for a theme choice unless they explicitly want to choose.
4. Apply tokens consistently to the artifact only. Preserve its content, information hierarchy, file format, and existing generation or verification workflow.
5. Check readability and contrast in the rendered or previewed result. Target WCAG AA contrast: 4.5:1 for normal text and 3:1 for large text or meaningful graphical elements. Do not rely on color alone to convey meaning.

## Boundaries

- Limit application to slide decks, reports, PDF or document covers, and other static stakeholder artifacts.
- Do not apply this skill to Next.js, websites, application screens, product UI, or repository-wide design systems.
- Do not override `DESIGN.md`, brand specifications, templates, or supplied assets.
- Do not download fonts, images, presets, packages, or other dependencies.
- Do not require extra model or tool calls beyond the already-selected host artifact creation, editing, and verification workflow. Do not add routing, orchestration, approval, or gate authority.
- Keep decoration subordinate to content. Prefer legible type, restrained accents, clear spacing, and repeatable hierarchy.

## Report the Result

Include this compact record with the delivered artifact or edit:

```text
Theme: <Project brand or theme name>
Tokens: <colors and font stacks actually used>
Scope: <artifact and styled regions>
Accessibility: <contrast/readability checks performed and result>
```

If a required contrast check cannot be performed, state that limitation instead of claiming compliance.

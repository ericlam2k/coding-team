# Upstream attribution

This addon adapts concepts from [`phuryn/pm-skills`](https://github.com/phuryn/pm-skills) at commit `18468a95b427e70e258b51389796367c6f684e7d` under the included MIT license.

## Sources

- `pm-product-discovery/skills/identify-assumptions-existing/SKILL.md`
- `pm-product-discovery/skills/identify-assumptions-new/SKILL.md`
- `pm-product-discovery/skills/prioritize-assumptions/SKILL.md`
- `pm-product-discovery/skills/brainstorm-experiments-existing/SKILL.md`
- `pm-product-discovery/skills/brainstorm-experiments-new/SKILL.md`
- `pm-execution/skills/wwas/SKILL.md`
- `pm-execution/skills/outcome-roadmap/SKILL.md`

## Transformations

- Created two narrow, explicit-only skills instead of importing upstream workflows.
- Removed automatic continuation, implementation direction, file/tool use, and model or role selection.
- Limited each artifact to 250 words and required a named human decision or stop reason.
- Reused existing coding-team `wwas` and `outcome-roadmap` rather than copying them.

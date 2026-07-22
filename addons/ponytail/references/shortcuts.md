# Intentional shortcuts (`ponytail:`)

When you take a deliberate shortcut (temporary stub, simplified path, deferred edge case):

1. Name it with a `ponytail:` marker in a comment or brief note.
2. State the **naming ceiling** (what this must never become without redesign).
3. State the **upgrade path** (what replaces it and when).

Example:

```ts
// ponytail: in-memory cache only — ceiling: single-instance; upgrade: shared Redis when multi-instance ships
```

Never use `ponytail:` to hide skipped security, privacy, or data-loss protection.

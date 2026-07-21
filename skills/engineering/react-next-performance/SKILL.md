---
name: react-next-performance
description: Apply focused React 19 and Next.js 15 App Router performance practices when writing, reviewing, or refactoring application UI, routes, and data access in Career Intelligence. Use with existing repository rules; do not add dependencies or speculative complexity.
version: 1.0.0
---

# React and Next.js Performance

Use for React/Next implementation, refactoring, performance review, and data-fetching work. Repository reality and `.clinerules` override generic guidance. Optimize a demonstrated bottleneck or preserve a known good default; do not add complexity without need.

## Priority order

1. Preserve security, Master of Truth, PII, CSP, consent, correctness, and accessibility rules.
2. Preserve RSC-first architecture: small leaf Client Components only where browser APIs or interaction require them.
3. Remove network and server-work waterfalls before tuning renders or JavaScript loops.
4. Reduce client JavaScript and server-to-client serialization before adding memoization.
5. Profile or establish a visible scale issue before micro-optimizing.

## Server and route work

- Start independent server/API operations early and await them together with `Promise.all` only when neither depends on the other.
- Keep `await` inside branches when a result is needed only in that branch.
- Stream independent slow regions with route-level `loading.tsx` or narrowly scoped `<Suspense>` fallbacks that reserve stable layout.
- Use `React.cache()` only for demonstrable duplicate request-scoped reads. Do not add cross-request caches, LRU packages, or cache layers without invalidation, data-safety, and repository approval.
- Minimize and explicitly shape serializable props crossing Server-to-Client boundaries. Never pass MoT or unnecessary candidate/CV PII to clients.
- Authenticate server actions with the same rigor as API routes. Preserve existing route auth, rate-limit, validation, and error-handling patterns.

## Bundle and third-party work

- Import known modules directly rather than through barrel files when bundle inspection identifies a cost.
- Use `next/dynamic` for genuinely heavy, client-only, or feature-gated UI. Keep existing Suspense/fallback behavior layout-stable.
- Load a module only when its feature is activated; preload on intent only when it improves a measured or clearly perceptible interaction.
- Defer nonessential analytics, logging, or third-party code until after hydration only when product requirements, consent, and the configured CSP allow it.
- Do not add SWR, `better-all`, LRU/cache packages, or any dependency solely to follow this skill. Follow the project dependency-approval rule.

## Client state and rendering

- Derive values during render instead of duplicating them in state or synchronizing them with effects.
- Move interaction-only logic to event handlers, not effects.
- Use primitive, semantically complete effect dependencies. Split effects/hooks only when their dependencies or lifecycles are independent.
- Use functional state updates when they keep callbacks stable; use lazy `useState` initialization for expensive initial values.
- Extract expensive subtrees into memoized components only when rerender cost is demonstrated. Do not memoize trivial expressions.
- Do not declare React components inside another component body.
- Use `startTransition` or `useDeferredValue` only for visibly expensive, non-urgent updates; never defer correctness-critical feedback.
- Deduplicate global event listeners and use passive listeners for scroll/touch listeners when cancellation is not needed.

## Rendering and JavaScript

- Continue using `next/image` with explicit dimensions for image rendering.
- For long, off-screen lists, consider `content-visibility` only after verifying browser behavior and UX/accessibility impact.
- Hoist static JSX, regular expressions, and stable non-primitive defaults when doing so prevents real repeated work or identity churn.
- Prefer `Map`/`Set` for repeated membership/lookups and combine repeated collection passes only where profiling or input scale justifies it.
- Prefer immutable non-mutating operations such as `toSorted()` when supported by the target runtime and appropriate for the surrounding code.

## Explicit exclusions

Do not introduce React Activity, `after()`, hydration-warning suppression, inline hydration scripts, SWR, `better-all`, or a new caching abstraction merely because they appear in generic performance guidance. Adopt one only after confirming installed-version support, product need, CSP/security compatibility, and repository conventions.

## Validation

For performance-sensitive changes, run the smallest relevant existing validation first, then the required wider check for changed scope: `npm run typecheck`, `npm run build`, existing self-checks, or `npm run test:ui`. Inspect the actual bundle/runtime behavior when the change claims a bundle, loading, or rendering benefit.

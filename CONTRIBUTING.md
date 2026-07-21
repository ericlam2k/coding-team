# Contributing

Thanks for contributing to **coding-team**.

## Ground rules

1. Keep **core/** platform-agnostic — no host model slugs, no product-specific policy.
2. Put runtime binding only under **adapters/**.
3. Do not raise WIP above 2 in policy docs without an ADR-style note.
4. Preserve third-party licenses in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
5. Prefer small PRs: one adapter fix, one docs chapter, or one skill update.

## Pre-publish checklist (maintainers)

- [ ] Hallmark redistribution rights confirmed (or switched to submodule)
- [ ] No absolute personal paths (`/Users/...`) in tracked files
- [ ] No product-specific secrets or private project policy leaked into `core/`
- [ ] `install.sh --platform codex --refresh-map` works on a clean Codex home
- [ ] README quickstart clone URL matches the public repo

## Dev setup

```bash
git clone https://github.com/ericlam2k/coding-team.git
cd coding-team
./install.sh --platform codex --global --refresh-map
```

## PR process

1. Open an issue for design/policy changes when possible.
2. Fork / branch from `main`.
3. Update docs if behavior or definitions change.
4. Fill the PR template.

## Code of conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

# Model routing

Use premium reasoning for decisions and economical models for bounded execution.

```text
premium think → eco build → evidence when needed
```

Model choice is guidance, never a workflow prerequisite. Record the actual model
when the host exposes it; do not block work when it does not.

## Codex owner profile

This optional Codex profile is explicit host metadata. Use it only when the
exact route is available; record planned and actual identity separately.

| Work | Primary / effort | Fallback / effort |
|---|---|---|
| Premium decision and Gatekeeper | `gpt-6-astra` / high | `claude-opus-5` / high |
| Frontend UX or visual work | `gpt-6-astra` / high | `claude-opus-5` / high |
| Frontend Builder | `OR-Laguna` / medium | `claude-sonnet-5` / medium |
| Backend system work and System Architect | `claude-fable-5.1` / high | `gpt-6-astra` / high |
| Code Reviewer | `gpt-5.6-luna` / high | `gpt-6-astra` / high |
| Test Engineer scenario design | `claude-sonnet-5` / high | `gpt-6-astra` / high |
| Test implementation | `gpt-5.6-luna` / medium | `claude-sonnet-5` / medium |

`gpt-5.6-sol` and `gpt-5.5` are excluded from this profile. `OR-Laguna` and
`claude-fable-5.1` require those exact configured routes. Do not substitute
Laguna XS, an alias, or another Fable version; route unavailability returns to
Lead for the named fallback on a new authorized route, never automatic retry.

## Role routing

| Work | Role | Capability |
|---|---|---|
| Fact finding | Investigator | economical |
| Product decision | Product Manager | premium |
| Shared contract | System Architect | premium |
| Technical direction or challenge | Advisor / Contradictor | premium |
| Implementation | Backend Engineer / Frontend Builder | economical capable builder |
| UX contract | Frontend UX Lead | premium when ambiguous, otherwise economical |
| Code inspection | Code Reviewer | careful validator |
| Runtime evidence | Test Engineer | careful validator |
| Final material acceptance | Gatekeeper | independent premium judgment |
| Documentation | Docs Steward | economical |

Choose the lowest-cost capable model. Escalate only when evidence conflicts,
the task crosses a material contract, or risk justifies stronger judgment.
Never retry by hopping models without changing the task or evidence.

## Related-role rule

Start with the single accountable role. Add another role only for one unresolved
question that can change the result. A filename, framework label, or preferred
model tier does not create a role requirement.

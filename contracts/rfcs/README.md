# Spec RFCs

Draft RFCs for GMP core-v3 contract changes proposed from [ARIAPlatform](https://github.com/brettin/ARIAPlatform_v0) alignment work. Open one PR per RFC; track gap IDs from the platform [`spec-implementation-gap-register.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/spec-implementation-gap-register.json).

| RFC | Title | Priority | Disposition |
| --- | --- | --- | --- |
| [001](001-run-invocation-and-tool-use.md) | Run invocation I/O and MAG tool_calls | P0 | — |
| [002](002-tool-call-events-vs-llm-tool-use.md) | tool.call events vs LLM tool-use | P0 | — |
| [005](005-events-append-list.md) | Events append/list DTO | P1 | — |
| [003](003-run-status-vocabulary.md) | Run status enum | P1 | — |
| [004](004-budgets-allocate-enforce.md) | Budget allocate and enforce | P1 | — |
| [006](006-capability-registry-platform.md) | Capability registry vs spec Capability | P2 | — |
| [010](010-run-cancelled-enum.md) | Add `run.cancelled` lifecycle event | P1 | Ship |
| [011](011-run-document-extensibility.md) | Reconcile Run `additionalProperties` with `extensionPolicy` | P2 | Issue |
| [012](012-tool-call-extensibility.md) | `tool.call` payload accounting fields | P2 | Hold |
| [013](013-failure-class-not-implemented.md) | Add `F9_NOT_IMPLEMENTED` failure class | P1 | Ship |
| [014](014-policy-eval-fixtures.md) | Starter fixtures for policy/eval ops | P1 | Ship |
| [015](015-conformance-stub-semantics.md) | Whether HTTP 501 stubs count as conformant | P2 | Issue |

Disposition notes (from platform conformance gaps, verified 2026-07-16):

- **Ship** — additive schema/fixture changes; open as a prescriptive RFC PR.
- **Issue** — real gap, but resolution is a maintainer call; raise as discussion first.
- **Hold** — blocked on RFC 011 and RFC 004 settling (012); 013 bundles naturally with 015.

### Impact map (010–015)

| RFC | Importance | Consequence |
| --- | --- | --- |
| **010** | High (Ship, clear gap) | Low (one enum value) |
| **011** | Medium (needs discussion) | Highest (extensibility precedent) |
| **012** | Medium (blocked on 011/004) | High (accounting surface) |
| **013** | High (Ship) | Medium (taxonomy honesty) |
| **014** | High (Ship, easy win) | Low (fixtures only) |
| **015** | Medium (Issue first) | Highest (governance of conformance) |

## Suggested merge order

1. RFC 001 — Run invocation I/O and MAG `tool_calls`
2. RFC 002 — `tool.call` events vs LLM tool-use
3. RFC 005 — Events append/list DTO
4. RFC 003 — Run status vocabulary
5. RFC 004 — Budget allocate and enforce
6. RFC 006 — Capability registry vs spec `Capability`
7. RFC 010 — Add `run.cancelled` lifecycle event
8. RFC 013 — Add `F9_NOT_IMPLEMENTED` failure class
9. RFC 014 — Starter fixtures for policy/eval ops
10. RFC 011 — Run document extensibility (discussion → PR)
11. RFC 015 — Conformance stub semantics (pairs with 013)
12. RFC 012 — `tool.call` accounting fields (after 011 + 004)

Until an RFC merges, platform v0 may continue to document wire behavior in [`platform-v0-implementation-profile.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/platform-v0-implementation-profile.json).

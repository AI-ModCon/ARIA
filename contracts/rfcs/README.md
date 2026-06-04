# Spec RFCs

Draft RFCs for GMP core-v3 contract changes proposed from [ARIAPlatform](https://github.com/brettin/ARIAPlatform_v0) alignment work. Open one PR per RFC; track gap IDs from the platform [`spec-implementation-gap-register.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/spec-implementation-gap-register.json).

| RFC | Title | Priority |
| --- | --- | --- |
| [001](001-run-invocation-and-tool-use.md) | Run invocation I/O and MAG tool_calls | P0 |
| [002](002-tool-call-events-vs-llm-tool-use.md) | tool.call events vs LLM tool-use | P0 |
| [005](005-events-append-list.md) | Events append/list DTO | P1 |
| [003](003-run-status-vocabulary.md) | Run status enum | P1 |
| [004](004-budgets-allocate-enforce.md) | Budget allocate and enforce | P1 |
| [006](006-capability-registry-platform.md) | Capability registry vs spec Capability | P2 |

## Suggested merge order

1. RFC 001 — Run invocation I/O and MAG `tool_calls`
2. RFC 002 — `tool.call` events vs LLM tool-use
3. RFC 005 — Events append/list DTO
4. RFC 003 — Run status vocabulary
5. RFC 004 — Budget allocate and enforce
6. RFC 006 — Capability registry vs spec `Capability`

Until an RFC merges, platform v0 may continue to document wire behavior in [`platform-v0-implementation-profile.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/platform-v0-implementation-profile.json).

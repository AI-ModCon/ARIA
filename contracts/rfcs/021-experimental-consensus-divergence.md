# RFC 021: Demote resolveAgentConsensus and listDivergenceAlerts to experimental

## Problem

`resolveAgentConsensus` (`POST /v3/agents/{agentId}/consensus`,
[`consensus-decision.schema.json`](../schemas/common/consensus-decision.schema.json)) and
`listDivergenceAlerts` (`GET /v3/supervision/alerts`,
[`divergence-alert.schema.json`](../schemas/common/divergence-alert.schema.json)) are
`requiredOperations` in [`profiles/core-v3.json`](../profiles/core-v3.json), but have no
known implementation (including ARIAPlatform_v0) and only canned fixtures
(`fixtures/v3/consensus-decision.response.json`, `divergence-alert.response.json`).
Mandating unproven operations in GA invites checkbox implementations. The consensus shape
is also unproven as a contract: the request body is a completed `ConsensusDecision`
(`result`, `decidedAt` required), so the operation records a decision rather than
resolving one.

## Proposal

- Move both to `/v3/experimental/` routes, consistent with the extension policy in
  `core-v3.json` (`x-gmp-*` fields or `/v3/experimental/*` routes); under RFC 016
  tiering they land in the `coordination` and `supervision` modules marked experimental.
- Removing required operations is contract-major per
  [`v3-release-governance.md`](../v3-release-governance.md), so the profile change
  sequences with the v4 profile turn; within v3, mark both deprecated-pending-demotion in
  release notes.
- Graduation back to core follows the existing experimental graduation path (profile
  update, path promotion, fixtures, release note) **plus a new bar this RFC proposes**:
  two independent interoperating implementations. (The governance doc currently sets no
  implementation-count requirement.)

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §5.6.

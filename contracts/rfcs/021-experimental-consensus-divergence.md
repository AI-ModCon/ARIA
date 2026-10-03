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
  tiering they are listed as `experimentalOperations` of the `coordination` and
  `supervision` modules (never `requiredOperations`, and excluded from every conformance
  level including C4).
- Removing required operations is contract-major per
  [`v3-release-governance.md`](../v3-release-governance.md), so the profile change
  sequences with the v4 profile turn; within v3, mark both deprecated-pending-demotion in
  release notes.

### Graduation bar (amends the governance doc)

`v3-release-governance.md` currently defines graduation as profile update, path
promotion, fixtures, and a release note, with no implementation-count requirement. **This
RFC adds a paragraph to `v3-release-governance.md`** making the experimental-to-core bar
for these (and future) experimental operations:

1. **Two implementations in separate codebases.** Not two deployments of one codebase,
   and not a reference implementation plus its own test client.
2. **Interoperation on shared fixtures.** The implementations demonstrate conformance by
   exchanging the same fixture set — each accepts requests the other produces — rather
   than each demoing against its own stub.
3. **Contract shape fixed before graduation.** For `resolveAgentConsensus` specifically:
   the request MUST become a consensus *proposal* (participants, options, decision
   policy) and the response the resulting
   [`ConsensusDecision`](../schemas/common/consensus-decision.schema.json). Graduating
   the current request shape would lock in a recorder of an already-made decision, which
   is not the operation's stated purpose.

`listDivergenceAlerts` graduates under bars 1 and 2; it does not share the request-shape
repair in bar 3.

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §5.6.

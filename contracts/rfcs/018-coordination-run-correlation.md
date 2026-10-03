# RFC 018: Run correlation on AgentMessage and Handoff

## Problem

[`agent-message.schema.json`](../schemas/common/agent-message.schema.json) and
[`handoff.schema.json`](../schemas/common/handoff.schema.json) both set
`additionalProperties: false` and define no `runId`, `correlationId`, or budget/authority
fields. Events carry `correlationId`; coordination records cannot. Work done on behalf of
a Run via `sendAgentMessage` / `handoffAgentTask` is uncorrelatable with that Run's
journal, and handoff authority attenuation has no field to live in. `AgentMessage.payload`
is an open object, so an envelope convention could carry correlation for messages — but
`Handoff` has no payload field at all, so no convention can rescue handoffs.

## Proposal

- Add optional `runId` and `correlationId` (`type: string`, `minLength: 1`) to both
  schemas. Additive; existing fixtures (`fixtures/v3/agent-message.request.json`,
  `fixtures/v3/handoff.request.json`) remain valid.
- Add optional attenuation references to `Handoff`: `capabilityTokenRef` (a
  [`capability-token.schema.json`](../schemas/common/capability-token.schema.json)
  `tokenId` the receiving agent operates under) and `budgetRef` (the
  [`budget-policy.schema.json`](../schemas/common/budget-policy.schema.json) `budgetId`
  returned by `allocateBudget` — not a usage-meter id). Attenuation semantics stay in the
  token (`scope`, `delegation`); the handoff only references them.
- Normative: **a handoff that sets `capabilityTokenRef` does not grant that token.** The
  receiving workload must present the referenced token and pass the ordinary use-time
  check — bearer is the token `subject`, token unexpired, token unrevoked, delegator
  still entitled. The handoff record is a pointer for audit and correlation, never a
  credential.
- Normative rule: when emitted in the context of a Run, `runId` MUST be set and
  `correlationId` SHOULD match the `correlationId` on the corresponding `appendEvent`
  envelopes (the event envelope's correlation field, not an ad hoc payload key), so
  journal queries reconstruct cross-agent causality.
- Rejected alternative: a blessed `payload` envelope — impossible for `Handoff` (no
  payload field) and invisible to schema validation.

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §5.3.

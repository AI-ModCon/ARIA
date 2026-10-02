# RFC 020: Make AgentMessage.expiresAt optional and define expiry semantics

## Problem

[`agent-message.schema.json`](../schemas/common/agent-message.schema.json) lists
`expiresAt` in `required`, forcing a TTL on every agent message — yet no expiry semantics
are defined anywhere: `sendAgentMessage` (`POST /v3/agents/{agentId}/messages`) returns
`202 AcceptedNoContent` with no expiry-related behavior, and no event type covers message
expiry. The spec's other `expiresAt` fields
([`capability-token.schema.json`](../schemas/common/capability-token.schema.json),
[`resume-token.schema.json`](../schemas/common/resume-token.schema.json)) have enforceable
meaning; this one does not. Most agent transports (including Academy mailboxes) have no
message TTL, so adapters will fill arbitrary far-future timestamps.

## Proposal

- Remove `expiresAt` from `required` (loosening change; existing payloads, including
  `fixtures/v3/agent-message.request.json`, remain valid).
- Define semantics when present: a deliverer MUST NOT deliver a message after
  `expiresAt`; an expired undelivered message is dropped and SHOULD be journaled via
  `appendEvent` with the message's correlation (see RFC 018 for `correlationId`).
- Absent `expiresAt` means no TTL.

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §5.5.

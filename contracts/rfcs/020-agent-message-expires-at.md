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
  `fixtures/v3/agent-message.request.json`, remain valid). Absent `expiresAt` means no
  TTL.
- **Obligated party.** The implementation that accepted the message at
  `sendAgentMessage` (the party that returned `202`) owns the expiry obligation: it MUST
  NOT deliver the message after `expiresAt`, and any transport it hands the message to
  acts on its behalf and inherits the same obligation. (The core has no deliver
  operation, so the obligation attaches to acceptance, not to an API call.)
- **Journaling, with a named event type.**
  [`event-envelope.schema.json`](../schemas/events/event-envelope.schema.json) is a
  closed `oneOf` and the `journal.*` `eventType` enum in
  [`journal-envelope-event.schema.json`](../schemas/events/journal-envelope-event.schema.json)
  is closed, so "SHOULD be journaled" needs a concrete branch. This RFC adds
  **`journal.message.expired`** to the journal `eventType` enum (landing on the v4 copy
  of the journal envelope schema, alongside the RFC 019 v4 event-envelope landing).
  Payload mapping under the existing closed journal payload (`runId`, `failureClass`
  required; `details` open):
  - `payload.runId` = the message's `runId` (RFC 018);
  - `payload.failureClass` = `F0_NONE` (expiry is an audit record, not a run failure);
  - `payload.details` = `{ "messageId": ..., "expiresAt": ..., "disposition":
    "expired_dropped" }`;
  - envelope `correlationId` = the message's `correlationId` (RFC 018).
- **Scope of the obligation.** The journaling SHOULD applies to run-correlated messages
  (those carrying `runId` per RFC 018). A message with no run context cannot satisfy the
  closed journal payload's required `runId`; for such messages, expiry journaling is
  OPTIONAL and deployment-specific. This limitation is stated rather than papered over;
  widening the journal payload is out of scope here.

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §5.5.

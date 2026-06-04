# RFC 005: Events append and list

## Problem

OpenAPI append references full `GmpEvent` oneOf. Platform append accepts `{ eventType, payload, runId?, ... }` and generates `eventId`/`occurredAt`.

List responses add top-level `runId`, `agentId`, `metadata`.

## Proposal

Document simplified append DTO as normative alternative or experimental profile; align list envelope rules.

# RFC 005: Events append and list DTO

**Gap IDs:** `op-appendEvent`, `op-listEvents`, `xevents-journal-payload` (related)

## Problem

The OpenAPI contract and the platform implementation have drifted on `/v3/events`:

- `appendEvent` in `contracts/openapi/gmp-core-v3.yaml` binds the request body to the
  full `GmpEvent` discriminated union
  ([`event-envelope.schema.json`](../schemas/events/event-envelope.schema.json)), a strict
  `oneOf` over six typed events (`run-lifecycle`, `policy-check`, `reasoning-node`,
  `tool-call`, `journal-envelope`, `classification-shift`). The platform accepts a looser
  `{ eventType, payload, runId?, agentId?, correlationId?, metadata?, source? }` shape and
  generates `eventId` / `occurredAt` server-side.
- List responses hoist `runId`, `agentId`, and `metadata` to envelope-level fields, while
  [`event-envelope-base.schema.json`](../schemas/events/event-envelope-base.schema.json)
  sets `additionalProperties: false` and does not define them at the top level — stored and
  listed objects do not currently validate against the spec.
- The spec documents `202 AcceptedNoContent` on append; the platform returns a body.
- The spec documents only `runId` / `eventType` list filters; the platform supports more.

## Proposal

`event-envelope.schema.json` remains the **single canonical wire contract for stored
events**. The simplified shapes on append and list are **projections** of that contract,
not a parallel DTO: append is a reduced input projection, list returns query projections.
The transitional client-side asymmetry is v0 migration drift, documented in
[`platform-v0-implementation-profile.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/platform-v0-implementation-profile.json)
with an explicit graduation criterion (removed at ARIAPlatform v1). No new
`CreateEventRequest` schema file is introduced.

### Normalization boundary (three-layer model)

1. **Append projection (client → server).** A reduced input shape carrying only fields the
   server cannot infer. The server maps it into the canonical envelope before persistence.
2. **Canonical stored record.** After server enrichment (`eventId`, `occurredAt`,
   `source`), the persisted object MUST validate against `event-envelope.schema.json`
   (the `oneOf` branch matching its `eventType`).
3. **List projection (server → client).** Responses return `EventListItem` objects, which
   MAY include query-index fields (`runId`, `agentId`, `metadata`) that are not part of the
   strict `GmpEvent` wire shape. These are a read-model convenience, not a second canonical
   contract.

## Append (`POST /v3/events`)

### Request: append projection

```json
{
  "eventType": "string (required)",
  "payload": "object (required)",
  "runId": "string (optional, top-level)",
  "agentId": "string (optional, top-level)",
  "correlationId": "string (optional, top-level)",
  "metadata": "object (optional, top-level)"
}
```

- Clients **MUST omit** `eventId`, `occurredAt`, and `source`.
- `payload` is opaque at the DTO level. Per-`eventType` payload shapes are defined
  normatively in `event-envelope.schema.json` and enforced server-side (see Validation).
- `runId` / `agentId` are query-index hints; the server MAY promote them into the typed
  payload per the matching `oneOf` branch or hold them as indexes, but the **stored**
  object must match the canonical schema.

### Server enrichment and `source` authority

| Layer | Normative rule |
| --- | --- |
| Append request | `source` is **not** a client field. It is omitted from the append DTO. |
| Server | MUST set `source` to a deployment-defined default (v0: `"gmp-server"`) or derive it from authenticated session context. The server MUST populate `eventId` and `occurredAt`. |
| Stored event | `source` is a **required top-level** field per `event-envelope-base.schema.json`. |
| List response | `source` is returned top-level, not buried inside `metadata`. |

### Validation

The server validates the normalized event against the `event-envelope.schema.json`
`oneOf`, selecting the branch by `eventType`. Invalid `eventType` values or malformed
payloads fail with `422 Unprocessable Entity` and a structured error pointing to the
offending field.

The append DTO carries the base envelope shape only. Journal-specific constraints
(per-`eventType` payload shapes flagged by gap `xevents-journal-payload`) are validated
server-side and surfaced as `422` responses on violation. Clients are not required to
vendor the journal schema; first-party clients MAY use typed models for pre-wire safety.

> Note: the platform today does not validate. This is new behavior, tracked as platform
> follow-up — not a claim of current compliance.

### Idempotency

Append is **at-least-once** from the client's perspective. The server does not
de-duplicate. Each accepted request produces a new `eventId` and a new journal entry,
even if the request body is byte-identical to a prior one. An optional `Idempotency-Key`
header is deferred to a future RFC.

### Response

```http
HTTP/1.1 201 Created
Location: /v3/events/evt_abc123
Content-Type: application/json

{"eventId": "evt_abc123"}
```

`POST /v3/events` returns `201 Created` on success, with a `Location` header pointing to
the canonical resource URL and a response body of `{"eventId": "..."}`. Servers MUST NOT
use `202 Accepted` for synchronous persistence: `event_store.record_event` persists
durably before the response returns, so there is nothing to poll for.

The `Location` header is **informational in v0** — it names the resource identity, not a
guarantee of a retrieve endpoint. There is no `GET /v3/events/{eventId}` operation today;
a future RFC may add `getEvent`.

## List (`GET /v3/events`)

### `EventListItem` (list projection)

| Field | Required | Notes |
| --- | --- | --- |
| `eventId` | yes | |
| `eventType` | yes | |
| `occurredAt` | yes | ISO-8601 |
| `source` | yes | top-level, server-authoritative |
| `payload` | yes | opaque object at DTO level; typed per `event-envelope.schema.json` `oneOf` branch |
| `correlationId` | no | top-level when present |
| `runId` | no | query index; MAY duplicate `payload.runId` |
| `agentId` | no | query index |
| `metadata` | no | deployment extensions and non-schema baggage (sidecar) |

`EventListItem` is defined in OpenAPI as the `items` element of `EventListResponse`; it is
not a new canonical schema. Each item would validate as a `GmpEvent` after stripping
`metadata` and normalizing index fields into the appropriate `oneOf` branch.

### `metadata` sidecar semantics

`metadata` is an optional append input and list output field for deployment-specific
extensions. It is **not** part of `event-envelope.schema.json`:

- On **append**, clients MAY supply `metadata: object`. The server stores it separately
  from the canonical envelope (v0: `extra` column) and returns it on list. It MUST NOT be
  merged into `payload` unless the typed event schema explicitly allows those keys.
- On **list**, `metadata` is returned top-level on `EventListItem` when present.
- On the **canonical store**, `metadata` is excluded from schema validation — validate the
  envelope, carry `metadata` alongside.

### Ordering

`listEvents` returns events in ascending `(occurredAt, eventId)` order. `eventId` is the
stable tiebreaker because `occurredAt` has only millisecond resolution (concurrent bursts
collide) and cursor pagination is otherwise non-deterministic across pages. This matches
journal semantics — readers replay in causal order.

### Pagination

Responses are wrapped in an envelope:

```json
{
  "items": [ /* EventListItem[] */ ],
  "nextCursor": "opaque-string-or-null",
  "total": 1234
}
```

- `nextCursor` is opaque. The server encodes `(occurredAt, eventId)` internally; clients
  pass it back via `?cursor=...`. Absence of `nextCursor` (or `null`) means end-of-stream.
- `total` is optional and MAY be omitted for large journals (counting can be expensive).
- Clients SHOULD use `?cursor=...` for forward iteration. The `offset` and `limit` query
  parameters are supported for v0 convenience; `offset` is deprecated and MAY be removed
  in a future release.

### Filters (v0)

| Filter | Type | Semantics |
| --- | --- | --- |
| `runId` | string | Exact match |
| `eventType` | string | Exact match (single value) |
| `agentId` | string | Exact match |
| `since` | ISO-8601 timestamp | `occurredAt >= since` |
| `cursor` | opaque string | Resume from `nextCursor` |
| `limit` | int | Page size; default `100`, max `1000` |
| `offset` | int | Skip-N (**deprecated** — prefer `cursor`) |

Filters combine with **AND** semantics. v0 does not support OR, negation, multi-value
filters, range queries other than `since`, or payload-content search. Callers requiring
richer querying SHOULD use `listEvents` to page the journal and filter client-side, or
open an issue describing the use case for a future RFC.

## Deferred (out of scope for this RFC)

- **Typed payload DTO / discriminator** — promoting per-`eventType` payload contracts into
  the DTO via an `eventType` discriminator, code-generation strategy for typed clients,
  and backward-compatibility rules for new event types. Tracked as **RFC 007** (RFC 006 is
  capability registry).
- **Idempotency** — `Idempotency-Key` header semantics, TTL window, de-dup scope, and
  duplicate-detection response shape.
- **`getEvent`** — a `GET /v3/events/{eventId}` retrieve operation backing the `Location`
  header.
- **Richer list querying** — multi-value filters, `until` / range queries,
  payload-content selectors.
- **Machine-readable `422` error contract** so clients can present actionable validation
  errors.

## Platform v0 alignment (out of scope)

This RFC is normative for the contract; `ARIAPlatform_v0` converges in separate PRs after
it merges:

| Item | Current drift | Target |
| --- | --- | --- |
| Append `source` | Client sends; stored in `extra` | Reject/ignore client `source`; persist top-level |
| Schema validation | None on append | Validate against `event-envelope.schema.json` `oneOf` → `422` |
| Normalization | Hoisted fields stored as-is | Map append projection → canonical envelope before persist |
| Response code | `202` + `{status, eventId}` | `201` + `Location` + `{eventId}` |
| Ordering | `timestamp` only | `(occurredAt, eventId)` tiebreaker |
| Pagination | `offset`/`limit` only | Add `cursor` encode/decode + `nextCursor`/`total` in response |
| Client `append()` | Sends `source` | Omit `source`; optional `metadata` unchanged |
| Client `list()` | Reads `items` only | No break; may adopt `cursor` param later |

## Platform reference

[ARIAPlatform `platform-v0-implementation-profile.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/platform-v0-implementation-profile.json)
— `AppendEventRequest`, `EventResponse`, `EventListResponse`. The transitional append/list
asymmetry documented there graduates (is removed) at ARIAPlatform v1.

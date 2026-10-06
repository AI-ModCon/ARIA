# RFC 012: Formalize `tool.call` payload extension surface for accounting detail

**Gap IDs:** `provisional-gap-003` (provisional — replace before opening upstream)

**Status:** Ship (Option A). Implemented on the v3 line together with
[RFC 022](022-execution-attempt-companion.md) and
[RFC 010](010-run-cancelled-enum.md) as contract patch 3.0.3; see the
[Disposition](#disposition) section for why the original Hold was lifted.

## Problem

[`tool-call-event.schema.json`](../schemas/events/tool-call-event.schema.json)
`payload` has `additionalProperties: false` and admits five fields:

```
runId | toolName | status | latencyMs | tokenCost
```

`tokenCost` is a **single integer** — total tokens for the call. The schema
forbids:

- per-call input vs. output token split (`inputTokens`, `outputTokens`)
- model identifier (`modelId`)
- provider name (`provider` — e.g., `vertex`, `bedrock`, `openai`)
- per-call USD spend (`spendUsd`)
- routing tier used (`modelTier` per
  [`model-routing-policy.schema.json`](../schemas/common/model-routing-policy.schema.json))
- output uncertainty / confidence (`uncertainty` per
  [`uncertainty.schema.json`](../schemas/common/uncertainty.schema.json))
- external task attempt identity (`attemptId` per
  [RFC 022](022-execution-attempt-companion.md))

All seven are operationally required:

- **Accounting** (`getTaskUsage`, `allocateBudget`, `enforceBudget`,
  related to [RFC 004](004-budgets-allocate-enforce.md)) needs input/output
  split *and* model id *and* spend to compute meaningful cost. Sonnet and
  Haiku at the same `tokenCost` integer cost ~10× apart.
- **Reasoning observability** (`runEval`, `getEvalResult`) needs the routing
  tier to interpret eval scores (a Haiku eval result is not directly comparable
  to an Opus eval result on the same suite).
- **Per-call uncertainty** is `GAP-002` in
  [`GAP_DISPOSITION_REGISTER.md`](../GAP_DISPOSITION_REGISTER.md), already
  dispositioned as `spine_patch` on `eval-result` and reasoning payloads — but
  the same data attached to a `tool.call` is currently homeless.
- **Attempt attribution** ([RFC 022](022-execution-attempt-companion.md)) needs
  a `tool.call` to say which `ExecutionAttempt` it ran under; without it,
  telemetry for a retried Run cannot be split between the attempt that failed
  and the attempt that succeeded.

The standard workaround today is a sibling extension event (e.g.,
`x-gmp.tool.call.tokens`) with `relatedEventId` pointing back to the strict
`tool.call`'s `eventId`. Both events share `correlationId` + `runId` for
joins. This works but:

- Every consumer must learn a two-event join pattern.
- The sibling event isn't part of any canonical schema, so its shape is
  per-implementer — implementations will reinvent it differently.
- `GET /v3/events?eventType=tool.call` returns the strict event only; pulling
  accounting detail requires a separate filter or a payload-aware read model.
  `enforceBudget` callers need both halves of the data, which is exactly the
  kind of split the strict envelope was meant to prevent.

This RFC is the `tool.call`-specific follow-on to [RFC 011](011-run-document-extensibility.md);
the precedent set there should propagate to all event payload schemas in a
later sweep.

## Proposal

Two options. Option A is recommended for ergonomic alignment with the
already-dispositioned `GAP-002` (uncertainty as `spine_patch`, not as a
separate canonical event). Option B is the strict-schema-preserving
alternative.

### Option A — Add optional accounting fields to `tool.call.payload`

```diff
 "payload": {
   "type": "object",
   "required": ["runId", "toolName", "status", "latencyMs", "tokenCost"],
   "properties": {
     "runId": { "type": "string", "minLength": 1 },
     "toolName": { "type": "string", "minLength": 1 },
     "status": { "type": "string", "enum": ["started", "succeeded", "failed"] },
     "latencyMs": { "type": "integer", "minimum": 0 },
-    "tokenCost": { "type": "integer", "minimum": 0 }
+    "tokenCost": { "type": "integer", "minimum": 0 },
+    "inputTokens": { "type": "integer", "minimum": 0 },
+    "outputTokens": { "type": "integer", "minimum": 0 },
+    "modelId": { "type": "string", "minLength": 1 },
+    "provider": { "type": "string", "minLength": 1 },
+    "modelTier": { "$ref": "../common/model-routing-policy.schema.json#/properties/defaultTier" },
+    "spendUsd": { "type": "number", "minimum": 0 },
+    "uncertainty": { "$ref": "../common/uncertainty.schema.json" },
+    "attemptId": { "type": "string", "minLength": 1 }
   },
   "additionalProperties": false
 }
```

#### Semantics

- All eight new fields are **optional**. Implementations that cannot or do not
  want to populate them keep emitting the minimal five-field payload unchanged.
- `tokenCost` stays required as the total. `inputTokens + outputTokens` is
  **not** required to equal `tokenCost` — providers report differently;
  implementations should clamp negative values to zero.
- `spendUsd` is the provider-reported billable amount, not a normalized
  cross-provider estimate (deliberately leaves cost-modeling to consumers).
- `uncertainty` exists in the schema today
  ([`uncertainty.schema.json`](../schemas/common/uncertainty.schema.json)) but
  has no carrier on `tool.call`; this adds the carrier.
- `attemptId` is the `ExecutionAttempt.attemptId` the call was made under, for
  Runs that execute through an external task system. See the
  [RFC 022](022-execution-attempt-companion.md) coordination note below.

Backward-compatible — existing fixtures and emitters remain valid.

### Option B — Canonical `tool-call-detail-event.schema.json` sibling

Keep `tool-call-event.schema.json` strict. Add a new event type
`tool.call.detail` with the additional fields plus a required
`relatedEventId` pointing back to the parent `tool.call`. Add it to the
[`event-envelope.schema.json`](../schemas/events/event-envelope.schema.json)
`oneOf`.

#### Trade-offs

- **Pros:** zero change to the strict `tool.call` event; explicit two-event
  contract every implementer can rely on.
- **Cons:** every consumer that needs accounting detail does a two-event read;
  join discipline is the implementer's responsibility; emit-path failures
  become two-stage (the parent succeeds, the detail can fail silently).

### Recommendation

**Option A.** It collapses the join, keeps the schema honest about what the
field set actually represents, and matches the already-merged spirit of
`GAP-002`. Option B is a viable fallback if backward compatibility on the
existing five-field shape is paramount.

### Coordination with RFC 004 (resolved)

[RFC 004](004-budgets-allocate-enforce.md) is the agenda item for the budget
allocate/enforce contract, and this RFC originally deferred its field naming to
whatever RFC 004 chose. That dependency is **resolved without waiting**: v3
already has a settled spelling for per-call spend, and this RFC follows it
rather than inventing a third. [`usage-meter.schema.json`](../schemas/common/usage-meter.schema.json)
uses `externalSpendUsd` and [`budget-policy.schema.json`](../schemas/common/budget-policy.schema.json)
uses `maxSpendUsd`, so `spendUsd` is the consistent per-call name: a `tool.call`
`spendUsd` aggregates into `UsageMeter.externalSpendUsd` and is enforced against
`BudgetPolicy.maxSpendUsd`. Likewise `inputTokens` / `outputTokens` split the
existing `tokenCost` rather than renaming it, and `modelTier` is a `$ref` to
`ModelRoutingPolicy.defaultTier` rather than a parallel enum. If RFC 004 later
renames the budget surface, these names should follow it in the same pass.

### Coordination with RFC 022

[RFC 022](022-execution-attempt-companion.md) requires `tool.call` events to
carry an `attemptId` so telemetry can be attributed to a specific external task
attempt. That is impossible today for the same reason this RFC exists: the
`tool.call` payload is closed and has no open `details` object (unlike
[`journal-envelope-event.schema.json`](../schemas/events/journal-envelope-event.schema.json),
whose `payload.details` is open, which is where RFC 022's `journal.*` binding
lives). Adding `attemptId` to this RFC's Option A field list resolves RFC 022's
`tool.call` binding and changes `tool-call-event.schema.json` once instead of
twice. The two RFCs are implemented in a single turn for that reason.

### Disposition

**Ship (Option A).** This RFC was previously held pending RFC 011 and RFC 004.
Neither is a hard dependency:

- **RFC 011** ([#17](https://github.com/AI-ModCon/ARIA/pull/17)) is a precedent,
  not a blocker. It asks whether `Run` should admit `x-gmp-*` extension keys.
  Option A here adds *named optional fields* under a still-closed
  `additionalProperties: false`, which neither anticipates nor forecloses that
  decision. The deferred sweep of the remaining event payloads still waits on
  RFC 011.
- **RFC 004** is resolved by the existing naming convention above.

## Deferred (out of scope for this RFC)

- **Generalizing the rule to every event payload.** The same
  `additionalProperties: false` vs. `extensionPolicy` tension exists on
  `policy-check-event`, `reasoning-node-event`, `classification-shift-event`.
  [RFC 011](011-run-document-extensibility.md) sets the precedent on `Run`;
  this RFC follows for `tool.call`; a later RFC should sweep the rest.
- **Cross-provider cost normalization.** This RFC adds `spendUsd` as the
  provider-reported number; whether ARIA standardizes a normalization function
  (or a cost-conversion companion schema) is a separate question.
- **Streaming-call accounting.** Anthropic and Vertex streaming SDKs do not
  populate usage at the same iteration point as non-streaming calls. Whether
  `tool.call` should distinguish stream vs. non-stream emission is a separate
  accounting RFC.

## Platform v0 alignment (out of scope)

| Item | Current drift | Target (Option A) |
| --- | --- | --- |
| Per-call accounting | Sibling extension event (`x-gmp.tool.call.tokens`) | Optional fields on the canonical `tool.call.payload` |
| Provider/model identification | Carried in metadata or sibling event | First-class `provider`, `modelId`, `modelTier` |
| Per-call spend | Reconstructed from token counts × pricing | Provider-reported `spendUsd` |
| Per-call uncertainty | Has no carrier on `tool.call`; lives on related reasoning/eval payloads | First-class `uncertainty` ref on `tool.call.payload` |

## Platform reference

[ARIAPlatform `platform-v0-implementation-profile.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/platform-v0-implementation-profile.json)
— `ToolCallEvent`, `BudgetAllocate`, `EnforceBudget`. ARIAPlatform v0 sketches
the budget side of accounting but does not yet ground the per-call data the
budget endpoints need to do their job; this RFC closes that loop.

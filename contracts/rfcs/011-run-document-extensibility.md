# RFC 011: Reconcile `Run` `additionalProperties: false` with `extensionPolicy`

**Gap IDs:** `provisional-gap-002` (provisional — replace before opening upstream)

## Problem

core-v3 documents two contradictory rules for `Run`:

- [`run.schema.json`](../schemas/common/run.schema.json) sets
  `additionalProperties: false` on the top-level `Run` document.
- [`core-v3.json` `extensionPolicy`](../profiles/core-v3.json) explicitly permits
  implementations to carry their own data via `x-gmp-*` field-name prefixes.

In practice, the strict schema wins for wire conformance: any implementation
that puts an `x-gmp-foo` key directly on a Run fails JSON-Schema validation
against `run.schema.json`. Implementers face three unattractive choices:

1. **Drop the strict schema check.** Skip `additionalProperties: false` validation
   in the conformance harness — defeats the point of the schema.
2. **Move per-implementation domain payload off the Run document entirely.**
   Standard workaround today: per-implementation data lives on a sibling
   endpoint (e.g., `GET /v3/runs/{runId}/result`) with an out-of-band pointer
   field. Works, but every consumer of "the full Run picture" now does two
   round-trips, and Run + payload joins are awkward in audit queries.
3. **Vendor-extend the schema locally.** Fork `run.schema.json`, relax
   `additionalProperties` to `true` for the local conformance run. Diverges
   every implementer.

The contradiction also undermines `extensionPolicy` itself: if the canonical
document carrying the most extension-worthy data (per-implementation domain
payload) can't actually use `x-gmp-*`, the policy's stated permission is empty
in the most important case.

The same contradiction recurs on event payload schemas (`tool-call-event`,
`policy-check-event`, `reasoning-node-event`, `classification-shift-event`).
This RFC picks the precedent on `Run`; downstream RFCs (including our
[RFC 012](012-tool-call-extensibility.md)) follow the same shape once the `Run`
case is settled.

## Proposal

Two options are presented. Either resolves the contradiction. Option A is
recommended for ergonomic and policy-consistency reasons; Option B is the
strict-schema-preserving alternative.

### Option A — Permit `x-gmp-*` on `Run`

Change `run.schema.json`:

```diff
 {
   "type": "object",
   "additionalProperties": false,
   "properties": { ... }
+  ,
+  "patternProperties": {
+    "^x-gmp-": { "type": ["object", "string", "number", "boolean", "array", "null"] }
+  }
 }
```

#### Semantics

- Required and optional fields are unchanged.
- Implementations MAY add `x-gmp-<name>` keys for per-deployment data.
- Conformance validation continues to forbid arbitrary keys; only
  `x-gmp-*`-prefixed keys are admitted.

Backward-compatible — no existing Run document is invalidated.

### Option B — Formalize the sibling-payload pattern

Keep `run.schema.json` strict. Add a normative section to
[`v3-design-notes.md`](../v3-design-notes.md) codifying:

- Per-implementation domain payload MUST live at `GET /v3/runs/{runId}/result`
  or under `/v3/experimental/<capability>/{runId}` per `extensionPolicy`.
- The result endpoint's shape is governed by the implementation's
  `Capability.artifact` ref (an existing field on
  [`capability.schema.json`](../schemas/common/capability.schema.json)).
- A new optional Run field `resultRef: string` (URI) names the canonical
  location of the per-implementation payload, so a single Run fetch reveals
  where to go next.

Backward-compatible — `resultRef` is optional and additive.

### Recommendation

**Option A.** Rationale:

- `extensionPolicy` already promises the surface; Option A makes the promise
  real.
- The sibling-endpoint pattern is a *workaround* for the contradiction, not a
  feature worth canonizing. Adopting it spec-wide encourages proliferation of
  `/v3/runs/{runId}/<thing>` endpoints per implementation.
- Option A is a one-block schema change; Option B is documentation plus
  operational discipline that every implementer has to re-learn.

Both options resolve the contradiction; either is acceptable.

## Deferred (out of scope for this RFC)

- **Same contradiction on event payloads.**
  `tool-call-event.schema.json`, `policy-check-event.schema.json`, and others
  have the same `additionalProperties: false` vs. `extensionPolicy` conflict.
  [RFC 012](012-tool-call-extensibility.md) addresses `tool.call` specifically
  (the most pressing case for accounting telemetry); a general sweep covering
  all event payloads should follow once the `Run` precedent is set.
- **`x-gmp-*` key naming rules.** Collision avoidance across deployments,
  whether a deployment-id prefix is required, JSON Pointer reservation. Worth
  its own RFC if Option A is picked.
- **OpenAPI surface implications.** Auto-generated clients may strip unknown
  fields silently; documenting the round-trip-preservation contract for
  `x-gmp-*` is a follow-up.

## Platform v0 alignment (out of scope)

| Item | Current drift | Target |
| --- | --- | --- |
| Per-implementation Run payload | Vendor-extended schema or sibling endpoint | Option A: native `x-gmp-*` key under strict schema |
| Conformance harness | Often skips `additionalProperties: false` on Run | Validate strictly; `x-gmp-*` admitted via `patternProperties` |
| Sibling result endpoint | Implementer-defined (e.g., `/v3/runs/{runId}/result`) | Optional under Option A; canonical under Option B with `Run.resultRef` |

## Platform reference

[ARIAPlatform `platform-v0-implementation-profile.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/platform-v0-implementation-profile.json)
— `Run`, `extensionPolicy`. The platform profile today documents the
sibling-endpoint pattern as a workaround; this RFC formalizes one direction or
the other so implementers stop diverging on the workaround shape.

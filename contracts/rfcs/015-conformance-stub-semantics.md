# RFC 015: Clarify whether HTTP 501 stub endpoints count as conformant

**Gap IDs:** `provisional-gap-006` (provisional — replace before opening upstream)

## Problem

[`core-v3.json`](../profiles/core-v3.json) declares `requiredOperations` (38
across 15 tags) and `requiredSchemas`. The `complianceCheck` list includes
`required_operations_present`.

ARIA does not define what "present" means. Two readings are both defensible
from today's text:

1. **Strict.** "Present" means the operation actually executes the declared
   behavior. A 501 stub is not present.
2. **Surface.** "Present" means the operation appears in the OpenAPI surface
   with a documented request/response shape, even if the implementation
   returns `501 + StructuredError{code: "NOT_IMPLEMENTED", recoverable: false}`
   for now.

[`v3-release-governance.md`](../v3-release-governance.md) GA exit criteria
item 4 ("durable execution: pause/resume/checkpoint fixtures demonstrate
replay-safe identifiers") hints at the strict reading for `DurableExecution`,
but is silent on whether a deployment that hasn't reached GA can claim
conformance for the operations it has stubbed.

### Why it matters

- Implementations targeting the spine rationally ship stubs early to get the
  OpenAPI surface published, then fill in real behavior. Whether they can
  claim conformance during that period changes the release-cadence calculus.
- Consumers of conformance reports (auditors, downstream platform integrators)
  need a uniform answer or every report is incomparable.
- `extensionPolicy` permits experimental routes under `/v3/experimental/*`;
  this RFC's resolution should also clarify whether *experimental* routes
  count toward conformance.

Practical consequence today: every implementation reports its conformance
matrix slightly differently. A reader can reasonably interpret "501 +
StructuredError" as "conformant" if the surface reading is correct, or as
"unimplemented" if the strict reading is correct. Both readings live in the
wild.

## Proposal

Pick one resolution and document it normatively in `v3-release-governance.md`
and the `complianceCheck` description in `core-v3.json`. Resolution C is
recommended as the most honest and operationally useful answer.

### Resolution A — Surface reading

A 501 stub counts as `required_operations_present` if:

- the operation appears in the published OpenAPI surface with a complete
  request/response shape,
- the 501 response body validates as a `StructuredError` with
  `code: "NOT_IMPLEMENTED"` and `recoverable: false`, and
- the operation's `failureClass`, if applicable, is the new
  `F9_NOT_IMPLEMENTED` (see [RFC 013](013-failure-class-not-implemented.md)) —
  not a misleading approximation.

**Pro:** keeps `requiredOperations` a useful early-build metric.
**Con:** a 100%-stubbed implementation reports as conformant on this row even
though it does nothing.

### Resolution B — Strict reading

A 501 stub does **not** count. Conformance requires a non-501 response for at
least one valid request.

**Pro:** green badges mean something.
**Con:** penalizes incremental delivery; implementations either lie or stop
publishing the OpenAPI surface until everything is real.

### Resolution C — Tri-state conformance per operation

Add a third reporting state. The `core-v3.json` `complianceCheck`
`required_operations_present` row becomes a three-valued report per operation:

```
implemented   — non-501 response on a valid request, validates against schema
stubbed       — 501 + StructuredError{code: NOT_IMPLEMENTED, recoverable: false}
                and OpenAPI surface published; counts toward "surface
                conformance" but not "behavioral conformance"
absent        — no route registered, or 404 on a valid request
```

Implementations report both counts. A reviewer sees that a deployment has,
e.g., 22 implemented / 6 stubbed / 4 absent out of 32 in-scope operations and
can judge fitness for purpose. The single boolean `required_operations_present`
row in `complianceCheck` becomes a derived check ("implemented + stubbed =
all in-scope," with absent operations enumerated).

**Pro:** the report tells the truth. Discourages both under-reporting and
over-claiming.
**Con:** more text in conformance reports; downstream tooling that expects a
single boolean per operation needs an update.

### Recommendation

**Resolution C.** The surface vs. behavioral distinction is the actual
question implementers are asking; exposing it in the conformance report
eliminates the per-implementation discretion that produces incomparable
reports today.

### Relationship to RFC 013

[RFC 013](013-failure-class-not-implemented.md) proposes the
`F9_NOT_IMPLEMENTED` failure class. If both RFCs land, Resolution A and
Resolution C both gain a precise wire signal for the "stubbed" state — the
501 response carries `code: "NOT_IMPLEMENTED"` and any generated Run record
carries `failureClass: F9_NOT_IMPLEMENTED`, so the conformance reporter can
identify stubs deterministically.

## Deferred (out of scope for this RFC)

- **Conformance-report schema as a first-class artifact.** ARIA today has no
  canonical conformance-report shape. A future RFC could standardize a
  `conformance-report.schema.json` so implementations' matrices become
  machine-comparable.
- **Stub graduation criteria.** When does a stub *have* to become real? Today
  implicit; could be codified per operation in `core-v3.json` with a
  `stubAcceptableUntil` field or similar.
- **HTTP status mapping for not-implemented operations.** 501 vs. 404 vs. 405.
  This RFC picks 501 (matching most existing implementations) but does not
  adjudicate; a follow-up could nail it down explicitly.

## Platform reference

[ARIAPlatform `platform-v0-implementation-profile.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/platform-v0-implementation-profile.json)
— `complianceCheck`, `requiredOperations`. ARIAPlatform v0 publishes a
conformance posture per deployment but does not have a uniform vocabulary for
the stubbed-vs-implemented distinction; this RFC closes that gap so
deployments can be compared apples-to-apples.

# RFC 013: Add `F9_NOT_IMPLEMENTED` to `FailureTaxonomy`

**Gap IDs:** `provisional-gap-004` (provisional — replace before opening upstream)

## Problem

[`failure-taxonomy.schema.json`](../schemas/events/failure-taxonomy.schema.json)
defines nine classes, F0 through F8:

```
F0_NONE | F1_MISSING_ARTIFACT | F2_ENVIRONMENT | F3_DATA_ACCESS |
F4_POLICY | F5_UNSPECIFIED_CONFIG | F6_HPC_QUEUE | F7_RUNTIME |
F8_DOMAIN_ASSUMPTION
```

None of the nine cleanly captures the "the capability is declared but the
backend is not yet implemented" case that every implementation hits while
building toward full conformance. Operationally, this happens in three
distinct shapes:

1. **Stub endpoint returning HTTP 501.** ARIA's optional operations
   (`pauseRun`, `resumeRun`, `listRunCheckpoints`, sandbox/supervision ops)
   commonly ship as `501 + StructuredError{code: "NOT_IMPLEMENTED"}` until the
   underlying durable-execution or HITL work lands. Today implementations
   reach for `F5_UNSPECIFIED_CONFIG` as the closest existing class, but the
   semantics are wrong — there is no config to set; the feature is simply not
   built.
2. **Feature disabled by deployment flag.** A capability is implemented but
   turned off (e.g., LLM features without provider credentials, HITL routes
   when `ENABLE_HITL=false`). Today implementations either reuse
   `F5_UNSPECIFIED_CONFIG` (close, but conflates two ops concerns) or
   `F4_POLICY` (wrong — it isn't a policy decision, it's a deployment
   posture).
3. **Capability declared but smoke test failed.**
   [`capability.schema.json`](../schemas/common/capability.schema.json) already
   has a `status: smoke_test_failed` value, but the corresponding Run that
   *would* exercise the capability has no precise `failureClass` to record.

Three different operational states, all currently sharing one approximate
class. The ambiguity makes the `failure_taxonomy_consistent` conformance row
misleading: a deployment with 30 unimplemented stubs and a deployment with 30
misconfigurations both report `F5_UNSPECIFIED_CONFIG` and look identical to an
auditor.

## Proposal

Add one new class:

```diff
 "enum": [
   "F0_NONE",
   "F1_MISSING_ARTIFACT",
   "F2_ENVIRONMENT",
   "F3_DATA_ACCESS",
   "F4_POLICY",
   "F5_UNSPECIFIED_CONFIG",
   "F6_HPC_QUEUE",
   "F7_RUNTIME",
-  "F8_DOMAIN_ASSUMPTION"
+  "F8_DOMAIN_ASSUMPTION",
+  "F9_NOT_IMPLEMENTED"
 ]
```

### Semantics

- **`F9_NOT_IMPLEMENTED`** — the operation is declared in the
  `capability.schema.json` registry but the backend implementation is absent
  or disabled at the deployment. Distinct from `F2_ENVIRONMENT` (the
  environment is broken), `F4_POLICY` (a policy denied it), and
  `F5_UNSPECIFIED_CONFIG` (configuration is missing for an *implemented*
  capability).
- Paired with `HTTP 501 + StructuredError{code: "NOT_IMPLEMENTED",
  recoverable: false}` on the wire.
- A Run carrying `failureClass: F9_NOT_IMPLEMENTED` MUST also have
  `status: failed`.

Backward-compatible (no Run ever previously emitted F9; existing F5 emitters
keep working).

### Alternative considered: split F9 vs. F10

A single F9 conflates "never implemented" with "implemented but disabled." The
argument for splitting is auditability — a deployment can know how many of its
501s are missing code vs. deliberately gated. The argument against is taxonomy
proliferation: every additional class adds reporting overhead, and the
deployment knows the difference internally via its own feature flags. This RFC
proposes the single-class addition and leaves a possible
`F10_FEATURE_DISABLED` split to a follow-up RFC if demand emerges.

### Alternative considered: document `F5_UNSPECIFIED_CONFIG` overload

Lighter-touch: update the schema description for F5 to explicitly cover "not
implemented" alongside "misconfigured." Rejected because the words "unspecified
config" don't fit "no code exists" — the overload is what creates the auditor
confusion in the first place.

### Relationship to RFC 015

[RFC 015](015-conformance-stub-semantics.md) asks the higher-order governance
question: do 501 stubs count toward conformance at all? This RFC scopes purely
to the failure taxonomy and is useful regardless of how RFC 015 resolves —
even if stubs *do* count, the Runs they generate still need a non-misleading
`failureClass`.

## Deferred (out of scope for this RFC)

- **`F10_FEATURE_DISABLED` split** (see Alternative above).
- **`StructuredError` ⇄ `failureClass` mapping table.** Codifying which
  `StructuredError.code` values map to which `failureClass` would be useful
  but is a documentation/governance task, not a schema change.
- **Per-operation declaration of expected `failureClass` set.** A capability
  could in principle declare which failure classes its Runs can produce.
  Useful for static analysis; out of scope here.

## Platform reference

[ARIAPlatform `platform-v0-implementation-profile.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/platform-v0-implementation-profile.json)
— `FailureClass`, `StructuredError`. ARIAPlatform v0 stubs surface as 501 +
`code: "NOT_IMPLEMENTED"` today; this RFC adds the matching failure class so
the wire response and the Run record agree on the same vocabulary.

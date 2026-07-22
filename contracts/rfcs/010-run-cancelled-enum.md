# RFC 010: Add `run.cancelled` to `RunLifecycleEvent.eventType` enum

**Gap IDs:** `provisional-gap-001` (provisional — replace before opening upstream)

## Problem

[`RunLifecycleEvent.eventType`](../schemas/events/run-lifecycle-event.schema.json)
is a closed enum with six values:

```
run.submitted | run.started | run.target_failed |
run.retry     | run.completed | run.failed
```

There is no `run.cancelled` event type. However:

- The same schema's `payload.status` enum *does* include `cancelled`
  (`["queued", "running", "succeeded", "failed", "cancelled"]`).
- `Run.status` in [`run.schema.json`](../schemas/common/run.schema.json) likewise
  admits `cancelled`.

So a Run can transition into the `cancelled` state, but no first-class lifecycle
event records the transition. Implementations have two unattractive options:

1. **Emit `run.failed` with `payload.status: "cancelled"`.** Internally
   inconsistent (the `eventType` says failed; the status says cancelled);
   downstream consumers filtering on `eventType` will miscount failures.
2. **Emit a `JournalEnvelopeEvent` with `eventType: "journal.run.cancelled"`.**
   Preserves semantics but moves cancellation out of the lifecycle stream — any
   consumer that filters `eventType` with a `run.*` glob (the obvious thing to
   do) misses cancellations entirely.

Neither option satisfies the
[`reasoning_trace_queryable`](../profiles/core-v3.json) spirit of "every state
transition is queryable by a uniform event filter."

## Proposal

Add `run.cancelled` to the `RunLifecycleEvent.eventType` enum:

```diff
 "eventType": {
   "type": "string",
   "enum": [
     "run.submitted",
     "run.started",
     "run.target_failed",
     "run.retry",
     "run.completed",
-    "run.failed"
+    "run.failed",
+    "run.cancelled"
   ]
 }
```

### Semantics

- Emitted when a Run transitions from `queued | running` to `cancelled`.
- Cancellation is initiator-driven (operator, scheduler, parent workflow),
  distinct from `run.failed` (terminal error) and `run.completed` (terminal
  success).
- `payload.status` MUST be `"cancelled"`.
- `payload.failureClass` MUST be `F0_NONE` — cancellation is not a failure.
  (Implementations that want to distinguish "cancelled because upstream failed"
  emit `run.failed` with the appropriate `failureClass` instead.)
- All other `payload` fields keep their existing semantics: `runId` and
  `capabilityId` required; `targetOutcomes` optional.

No new schema file; this is an additive enum patch. Existing consumers will see a
new `eventType` value they may want to handle; no existing event shape changes.

### Relationship to RFC 003

[RFC 003](003-run-status-vocabulary.md) targets the `Run.status` enum vocabulary
(spec vs platform); this RFC targets the `RunLifecycleEvent.eventType` enum.
Both can land independently — RFC 003 reconciles status names, this RFC adds the
matching lifecycle event for the already-permitted `cancelled` status. If RFC
003 lands first and renames `cancelled` to a platform-aligned spelling, this
RFC's enum value should follow.

## Deferred (out of scope for this RFC)

- **Cancellation reason / initiator metadata.** A `payload.cancelledBy`
  (principal id) or `payload.cancellationReason` (free text) field would be
  useful but introduces shape questions beyond this enum-only patch.
- **`cancelRun` operation semantics.** The lifecycle event records that
  cancellation happened; what HTTP shape `cancelRun` takes (synchronous vs.
  202 + poll, hard vs. cooperative) is separately specified by the operation
  contract.
- **Mid-flight cancellation behavior** of cooperative checkpoint resumption
  (interaction with `pauseRun` / `resumeRun` / `listRunCheckpoints`). The
  durable-execution surface is its own RFC.

## Platform reference

[ARIAPlatform `platform-v0-implementation-profile.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/platform-v0-implementation-profile.json)
— `RunStatus`, `RunLifecycleEvent`. ARIAPlatform v0 surfaces a `cancelled` Run
status today; this RFC adds the matching lifecycle event so the transition is
auditable through the normal `listEvents` filter.

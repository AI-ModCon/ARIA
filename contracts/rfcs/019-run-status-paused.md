# RFC 019: Representing paused runs in the Run document

**Extends RFC 003 (run status vocabulary).**

## Problem

`pauseRun` (`POST /v3/runs/{runId}/pause`) is required by
[`profiles/core-v3.json`](../profiles/core-v3.json) and returns `WorkflowStateAccepted`,
and [`workflow-state.schema.json`](../schemas/common/workflow-state.schema.json) has
`paused` / `resumable` in its status enum — but the
[`run.schema.json`](../schemas/common/run.schema.json) `status` enum is only
`queued | running | succeeded | failed | cancelled`. A paused run is unrepresentable in
the `getRun` document without dereferencing the optional embedded `workflowState`. The
same gap exists in
[`run-lifecycle-event.schema.json`](../schemas/events/run-lifecycle-event.schema.json):
its payload `status` enum matches `run.schema.json`, and there are no `run.paused` /
`run.resumed` event types. (RFC 010 adds `run.cancelled` to the `eventType` enum; this
RFC adds the `paused` analogues.)

## Proposal

- Add `paused` to the `status` enum in the Run schema. This RFC supplies the concrete
  case; general rules for status-vocabulary growth defer to RFC 003.
- Add `paused` to the payload `status` enum and `run.paused` / `run.resumed` to the
  `eventType` enum in the run-lifecycle event schema.
- Mapping rule, stated as schema constraints rather than a biconditional over an optional
  field (`workflowState` is optional today, so without this a document could claim
  `paused` with no workflow state, or `running` while `workflowState.status` says
  `paused`):
  - `status: paused` REQUIRES `workflowState` to be present with
    `workflowState.status` ∈ {`paused`, `resumable`} — enforced with an in-schema
    `if`/`then` (`if status == paused then required: [workflowState]` plus the
    `workflowState.status` restriction).
  - `resumeRun` returns the Run `status` to `running`.
  - Run `status` does **not** distinguish `paused` from `resumable`; that distinction
    lives only on `workflowState.status`.
- `workflow-state.schema.json` is unchanged.

## Landing (file-level)

Per the v4 profile turn (RFC 016 versioning note), these edits land on **v4 copies**, not
in place: `schemas/v4/run.schema.json` and `schemas/v4/run-lifecycle-event.schema.json`.
Because the current [`event-envelope.schema.json`](../schemas/events/event-envelope.schema.json)
`oneOf` references `./run-lifecycle-event.schema.json`, a v4 lifecycle schema is invisible
to `appendEvent` until the envelope points at it: the landing therefore **also adds
`schemas/v4/event-envelope.schema.json`** whose `oneOf` references the v4 lifecycle
schema, and `gmp-core-v4.yaml` routes `appendEvent` / `listEvents` through that v4
envelope. The v3 files are untouched; existing v3 documents remain valid.

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §5.4.

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

- Add `paused` to the `status` enum in `run.schema.json`. This RFC supplies the concrete
  case; general rules for status-vocabulary growth defer to RFC 003.
- Add `paused` to the payload `status` enum and `run.paused` / `run.resumed` to the
  `eventType` enum in `run-lifecycle-event.schema.json`.
- Mapping rule: Run `status: paused` ⇔ `workflowState.status` ∈ {`paused`, `resumable`};
  `resumeRun` returns the Run to `running`. `workflow-state.schema.json` is unchanged.

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §5.4.

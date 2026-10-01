# RFC 022: ExecutionAttempt companion schema

## Problem

[`run.schema.json`](../schemas/common/run.schema.json) has no attempt identity: `retryRun`
(`POST /v3/runs/{runId}/retry`) exists, but attempts are unrepresentable — the Run carries
only `status`, `targets[].state`, and `currentCheckpointId`, and no `attemptId` appears
anywhere in `contracts/`. Three production external task systems need the same linkage:
Slurm/PBS jobs reached via IRI facility APIs, Globus Compute tasks, and Globus Transfer
tasks — each with its own task id, retry semantics, and event stream. Without a spec
answer, every adapter mints its own `x-gmp-*` extension and reinvents
reconciliation-after-restart ("one Run ↔ one scheduler job; restart converges; no
orphan").

## Proposal

Add `companion/schemas/execution-attempt.schema.json` (disposition `companion_spec`,
following the GAP-004 precedent of
[`data-movement-intent.schema.json`](schemas/data-movement-intent.schema.json)):

- `required`: `attemptId`, `runId`, `externalSystem`, `externalTaskId`, `createdAt`.
- `externalSystem`: object `{ type: enum [scheduler, globus_compute, globus_transfer,
  other], endpoint: uri }`; optional `externalTaskUri` (IRI-resolvable task/job URI).
- `status`: projection enum `[submitted, running, succeeded, failed, cancelled, lost]`
  plus `lastReconciledAt`; optional `supersedesAttemptId` (retries) and `idempotencyKey`
  echo from `submitRun`.
- Reconciliation semantics (normative): at most one non-terminal attempt per
  (`runId`, `externalSystem.type`); after restart the owning gateway MUST reconcile every
  non-terminal attempt against the external system before creating new attempts
  (converge to terminal state or mark `lost`); orphaned external tasks are journaled and
  cancelled per site policy.
- Linkage: event payloads reference `attemptId`; the artefact is linked from the Run like
  other companions. No core `run.schema.json` change in this RFC; an optional
  `currentAttemptId` on Run is deferred to an implementation-informed follow-up.
- Implementation PR adds the schema to `profiles/core-v3-companion.json` and fixtures
  under `fixtures/companion/`.

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §9.3.

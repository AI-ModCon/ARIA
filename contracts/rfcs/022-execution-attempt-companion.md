# RFC 022: ExecutionAttempt companion schema

## Problem

[`run.schema.json`](../schemas/common/run.schema.json) has no attempt identity: `retryRun`
(`POST /v3/runs/{runId}/retry`) exists, but attempts are unrepresentable — the Run carries
only `status`, `targets[].state`, and `currentCheckpointId`, and no `attemptId` appears
anywhere in `contracts/`. Three production external task systems need the same linkage:
Slurm/PBS jobs reached via IRI facility APIs, Globus Compute tasks, and Globus Transfer
tasks — each with its own task id, retry semantics, and event stream. Without a spec
answer, every adapter mints its own `x-gmp-*` extension and reinvents the restart
invariant: **at most one non-terminal attempt per (`runId`, `externalSystem.type`),
restarts converge on the existing external task, and no orphan survives unjournaled.**
(Retries are further attempts of the same Run, not a second job identity.)

## Proposal

Add `companion/schemas/execution-attempt.schema.json` (disposition `companion_spec`,
following the GAP-004 precedent of
[`data-movement-intent.schema.json`](../companion/schemas/data-movement-intent.schema.json)):

- `required`: `attemptId`, `runId`, `externalSystem`, `externalTaskId`, `createdAt`.
- `externalSystem`: object `{ type: enum [scheduler, globus_compute, globus_transfer,
  other], endpoint: uri }`; optional `externalTaskUri` (IRI-resolvable task/job URI).
- `status`: projection enum `[submitted, running, succeeded, failed, cancelled, lost]`
  plus `lastReconciledAt`; optional `supersedesAttemptId` (retries) and `idempotencyKey`
  echo from `submitRun`.

### Invariant and `retryRun` semantics (normative)

- At most one **non-terminal** attempt may exist per (`runId`, `externalSystem.type`).
  A new attempt for that pair may be created only when every prior attempt for it is in
  a terminal state (`succeeded`, `failed`, `cancelled`, `lost`).
- **`retryRun` appends a new `ExecutionAttempt` on the same `runId`**, with
  `supersedesAttemptId` set to the attempt it replaces. `retryRun` MUST NOT mint a new
  Run: Run identity is stable across retries, and attempt identity is what varies. (An
  implementation that creates a new Run on retry cannot record `supersedesAttemptId`
  against the original Run, so the two behaviors are mutually exclusive; this companion
  picks the former.)

### Reconciliation (normative, and copied into the schema `description`)

After a restart, the owning gateway MUST reconcile every non-terminal attempt against
its external system **before creating any new attempt**: converge the attempt to a
terminal state, or mark it `lost` with `lastReconciledAt` updated; orphaned external
tasks are journaled and cancelled per site policy. This text ships verbatim in the
schema's top-level `description`, not only in this RFC — it is the behavior that stops a
restart from double-submitting, and it must survive in the artefact implementers actually
read.

### Linkage and discovery

- **Lookup key.** The attempt carries `runId`; profiles adopting this companion state
  that **deployments MUST be able to list `ExecutionAttempt` artefacts by `runId`**.
  No new Run field is needed for discovery; an optional `currentAttemptId` on Run stays
  deferred to an implementation-informed follow-up.
- **Event binding.** The journal payload
  ([`journal-envelope-event.schema.json`](../schemas/events/journal-envelope-event.schema.json))
  is closed except for its open `details` object: `journal.*` events emitted while an
  attempt is active MUST carry **`payload.details.attemptId`**; `tool.call` events
  related to an attempt likewise carry `attemptId` in their payload. No event-envelope
  `oneOf` change is required.
- **Profile registration.** The schema is registered the way the other companions are
  required: the implementation PR adds it to
  [`profiles/core-v3-companion.json`](../profiles/core-v3-companion.json)
  `requiredSchemas` (and the v4 companion profile on the v4 turn), alongside
  `campaign-plan`, `data-movement-intent`, `eval-publication`, and `run-invocation`,
  with fixtures under `fixtures/companion/`.

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §9.3.

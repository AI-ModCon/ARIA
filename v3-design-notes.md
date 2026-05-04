# GMP v3 design notes

This document records the unification decisions for **core-v3**: a single OpenAPI surface under `/v3/...` that merges the former `core-v1` operational backbone and `core-v2` agent-native primitives. Historical `core-v1` and `core-v2` artifacts live under [archive/v1/](archive/v1/) and [archive/v2/](archive/v2/).

## 1. Identity (v1 token exchange + v2 capability tokens)

- **Session bootstrap**: `POST /v3/identity/sessions` (`establishSession`) replaces v1 `POST /v1/identity/token-exchange`. The response body is the [identity-session.schema.json](schemas/common/identity-session.schema.json) object (`accessToken`, `expiresIn`, `claims` referencing [identity-claims.schema.json](schemas/common/identity-claims.schema.json)).
- **Intent-scoped credentials**: v2 capability token mint, revoke, and audit remain as `POST /v3/identity/capability-tokens`, `POST /v3/identity/capability-tokens/revoke`, and `GET /v3/identity/capability-tokens/{tokenId}/audit`.
- **Shared model**: Capability token `subject` aligns with `IdentityClaims.principalId` so both flows compose without parallel identity models.

## 2. Run lifecycle (v1 submit/status/cancel/retry + v2 plan/pause/resume/checkpoints)

- All verbs share one `runId` path prefix: submit and read/cancel/retry under `/v3/runs` and `/v3/runs/{runId}`, plus negotiation `POST /v3/runs:plan`, durable `pause` / `resume` / `checkpoints` under the same resource tree.
- [run.schema.json](schemas/common/run.schema.json) gains optional `planId`, `currentCheckpointId`, and embedded optional `workflowState` ([workflow-state.schema.json](schemas/common/workflow-state.schema.json)) so a single Run document can carry durable-execution fields without a second resource type.

## 3. Errors (StructuredError everywhere)

- All v3 error responses use [structured-error.schema.json](schemas/common/structured-error.schema.json). The v1-only `ErrorResponse` component is not used on the v3 line.

## 4. Provenance and observability (journal + reasoning in one stream)

- **Unified path**: Append and query use `POST /v3/events` and `GET /v3/events` (replacing v1 `/v1/journal/events` and v2 `GET /v2/experimental/reasoning/events`).
- **Schema**: [event-envelope.schema.json](schemas/events/event-envelope.schema.json) is a **oneOf** union over [run-lifecycle-event](schemas/events/run-lifecycle-event.schema.json), [policy-check-event](schemas/events/policy-check-event.schema.json), [reasoning-node-event](schemas/events/reasoning-node-event.schema.json), [tool-call-event](schemas/events/tool-call-event.schema.json), and [journal-envelope-event](schemas/events/journal-envelope-event.schema.json).
- **Base fields**: Shared envelope fields live in [event-envelope-base.schema.json](schemas/events/event-envelope-base.schema.json); specialized types compose it via `allOf`.
- **Journal terminology preserved**: The v1 journal/provenance concept continues as the `journal.*` `eventType` family (for example `journal.run.completed`, `journal.policy.checked`). The HTTP path generalizes to `/v3/events`, but append-only audit semantics and the shared [failure-taxonomy.schema.json](schemas/events/failure-taxonomy.schema.json) are unchanged in intent.

## Cross-cutting policies

- **Extensions**: `core-v3.json` `extensionPolicy` requires `x-gmp-*` fields or routes under `/v3/experimental/*` for non-core extensions. The core OpenAPI document does not define experimental operations; implementations reserve that namespace for graduation from experiments to core.

### Campaign plans and portability

Spine Runs may reference an externally stored **CampaignPlan** JSON artefact (`planRef`, `planDigest`) defined under [companion/schemas/campaign-plan.schema.json](companion/schemas/campaign-plan.schema.json). This keeps orchestration semantics portable without expanding `planRun`'s synchronous response into a full graph schema.

### Mid-run classification shifts

Deployments may emit `classification.shift` events (see [schemas/events/classification-shift-event.schema.json](schemas/events/classification-shift-event.schema.json)) alongside existing envelope variants so observability tooling can correlate tier changes with `pauseRun`, supervision queues, and new policy evaluations.
- **Idempotency**: Profile check `idempotency_required_on_mutations` is carried from v2. `submitRun` carries `idempotencyKey` in the request body; other mutating operations should require an `Idempotency-Key` header (to be tightened in OpenAPI operation parameters in a follow-up pass if desired).
- **Failure taxonomy**: A single F0–F8 taxonomy is used across runs, legacy journal payloads, and envelope payloads.

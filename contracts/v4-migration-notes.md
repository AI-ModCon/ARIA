# GMP v3 → v4 migration notes (draft)

**Status: draft for review.** v3 (`core-v3`, API path `/v3/`) remains the GA line.
This v4 surface is additive alongside v3 — no v3 file changes — and lands only after
the federation council disposes the underlying RFCs. Per
[v3-release-governance.md](v3-release-governance.md), shrinking the flagship profile's
required operations is a contract-major action: hence a new `/v4/` API path and new
profile ids rather than a v3 minor.

## What changed and why

| Change | Where | RFC |
| --- | --- | --- |
| Profile tiering: 14-operation minimal core + 8 named optional modules + C0–C4 conformance levels | [profiles/core-v4-minimal.json](profiles/core-v4-minimal.json), [profiles/core-v4-modules.json](profiles/core-v4-modules.json), [profiles/federation-v4.json](profiles/federation-v4.json) | RFC 016 |
| `ExecutionContext.seedList` / `dataVersion` optional (placeholder values degrade provenance for non-simulation runs) | [schemas/v4/execution-context.schema.json](schemas/v4/execution-context.schema.json) | RFC 017 |
| Optional `runId`/`correlationId` on `AgentMessage` and `Handoff`; `capabilityTokenRef`/`budgetRef` on `Handoff` (authority attenuation now has a field to live in) | [schemas/v4/agent-message.schema.json](schemas/v4/agent-message.schema.json), [schemas/v4/handoff.schema.json](schemas/v4/handoff.schema.json) | RFC 018 |
| `paused` in Run status; `run.paused`/`run.resumed` lifecycle events (paused runs were unrepresentable in the Run document) | [schemas/v4/run.schema.json](schemas/v4/run.schema.json), [schemas/v4/run-lifecycle-event.schema.json](schemas/v4/run-lifecycle-event.schema.json) | RFC 019 |
| `AgentMessage.expiresAt` optional, with defined must-not-deliver-after semantics when present | [schemas/v4/agent-message.schema.json](schemas/v4/agent-message.schema.json) | RFC 020 |
| `resolveAgentConsensus` and `listDivergenceAlerts` demoted to `/v4/experimental/` (no known implementation; graduation requires two independent implementations) | [openapi/gmp-core-v4.yaml](openapi/gmp-core-v4.yaml), module descriptors | RFC 021 |
| `ExecutionAttempt` companion schema: one external-task-identity record (Slurm/PBS via IRI, Globus Compute, Globus Transfer) with reconciliation-after-restart semantics | [companion/schemas/execution-attempt.schema.json](companion/schemas/execution-attempt.schema.json) | RFC 022 |

The RFCs are filed as PRs #27–#33.

## Stub theater, and why tiering is the fix

`core-v3` makes all 38 operations mandatory, so a site gateway that faithfully
implements identity, runs, events, and policy must stub memory summarization and
consensus endpoints into "conformance." That destroys the profile's signal value
(see also RFC 015 on whether HTTP 501 stubs count as conformant). In v4 a deployment
claims the minimal core plus exactly the modules it implements, and the federation
profile binds conformance levels to evidence classes (`reference` → `cross-org-live`)
so live tiers cannot be claimed from reference-only passes.

## Versioning mechanics in this turn

- `openapi/gmp-core-v4.yaml`: derived from v3; `/v4/` paths, `info.version
  4.0.0-draft`, same 38 operationIds (2 now experimental).
- Changed schemas get v4 variants under `schemas/v4/` with `$id` under
  `…/schemas/v4/`; unchanged schemas stay in `schemas/common/` and `schemas/events/`
  and are referenced from both API versions. Internal `$ref`s in v4 variants point
  back to `../common/` / `../events/` except where the target also changed
  (`run.schema.json` → v4 `execution-context.schema.json`).
- Fixtures for every changed schema live under `fixtures/v4/`.
- `scripts/validate_v4_contracts.py` (stdlib-only, reuses the v3 validation engine)
  checks: operation-set parity with v3, experimental route placement, profile schema
  resolution, exact partition of the 38 operations across minimal/modules/experimental,
  federation levels referencing defined modules, fixture validation, and two negative
  checks proving the v4 loosenings are real (v4 fixtures must fail v3 schemas).
  Run `make validate-v4-contracts`; `make validate-v3-contracts` is unaffected.

## Migration posture for implementers

v4 is a strict superset of v3 semantics minus the two de-required experimental
operations: every valid v3 payload remains valid under the corresponding v4 schema,
and a `core-v3` deployment is exactly a v4 C4 deployment (plus the two experimental
operations it was already required to stub). Downgrading a claim from "all of v3" to
an honest module list is the intended migration.

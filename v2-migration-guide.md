# GMP v1 to v2 Migration Guide

This guide defines how to adopt `core-v2` while keeping `core-v1` deployments stable.

## Migration Strategy

1. Run `v1` and `v2` contracts in dual-stack mode.
2. Move high-risk workflows to v2 first (identity revocation, sandboxed actions, supervision).
3. Keep v1 consumers untouched until equivalent v2 fixture and profile checks pass.
4. Decommission v1 endpoints only after two stable v2 releases.

## Concept Mapping

| v1 Concept | v2 Concept | Migration Action |
| --- | --- | --- |
| Token exchange + delegation claims | Capability token + delegation intent + revocation | Add token mint/revoke/audit before privileged actions |
| Direct run submit | Negotiation planning + run control | Add `POST /v2/runs:plan` preflight before side effects |
| Run status and journal events | Workflow state/checkpoints + reasoning/tool events | Emit both legacy journal and v2 reasoning events during transition |
| App-specific memory logic | Managed memory records/policies | Move retention/sharing/compliance into memory policy fields |
| Infra-oriented spend reports | Usage meter + budget/model routing policies | Enforce budget rules using v2 `allocate` and `enforce` endpoints |
| Human approval as obligation text | Supervision queue + intervention records | Integrate queue consumers and intervention writers |

## Suggested Adoption Waves

### Wave 1: Identity and Negotiation
- Implement `mintCapabilityToken`, `revokeCapabilityToken`, and `getCapabilityTokenAudit`.
- Route new agent workflows through `planRun`.

### Wave 2: Durable + Memory + Budgets
- Add pause/resume/checkpoint support to long-running runs.
- Record memory via policy-governed APIs.
- Enforce token/tool-call budgets.

### Wave 3: Observability + Safety + Supervision
- Emit reasoning and tool-call events.
- Gate all side effects through propose/approve/apply/rollback.
- Activate supervision queue and divergence alerts.

## Exit Gates Per Wave

- OpenAPI references resolve with zero errors.
- All `core-v2` required operations are implemented.
- Fixtures in `contracts/fixtures/v2/` validate against schemas.
- Retry and replay behavior remains idempotent under concurrent load.
- Critical action paths require sandbox gate and intervention support.

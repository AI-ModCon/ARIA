# GMP v2 Release Governance

This document defines readiness and release governance for `core-v2`.

## Release Cadence

- Minor releases are additive only.
- Any breaking change requires `v3` planning and migration notes.
- Experimental features must stay under `/v2/experimental/*` until graduated.

## Graduation Policy for Experimental Endpoints

An endpoint graduates from experimental status only when:

1. It is listed in `profiles/core-v2.json` `requiredOperations` (if core) or documented as optional.
2. It has validated fixture coverage.
3. Structured error semantics are complete (`recoverable`, `nextBestAction`, `missingInputs`).
4. Security and idempotency checks pass.

## GA Exit Criteria

`core-v2` is GA-ready only when all criteria pass:

1. `contracts/openapi/gmp-core-v2.yaml` validates with no unresolved references.
2. `contracts/profiles/core-v2.json` required operations and schemas are fully implemented.
3. Revocation and delegation tests pass under concurrent retries.
4. Pause/resume/checkpoint replay determinism tests pass.
5. Memory retention and forgetting policies pass compliance checks.
6. Budget allocation/enforcement behaves correctly under threshold pressure.
7. Reasoning and tool-call event chains are queryable end-to-end.
8. Agent coordination handoff and consensus scenarios pass.
9. Sandbox propose/approve/apply/rollback scenarios pass.
10. Supervision queue, alerts, and intervention record scenarios pass.

## Release Checklist

- Validate OpenAPI + JSON schemas.
- Validate all v2 fixtures against referenced schemas.
- Run profile compliance checks for `core-v2`.
- Publish migration deltas from previous release.
- Update compatibility matrix in `contracts/README.md`.
- Record known limitations and rollout guards.

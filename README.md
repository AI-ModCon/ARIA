# GMP Contracts (core-v3)

This directory defines the **Genesis Mission Platform (GMP) core-v3** contract baseline: one OpenAPI surface under `/v3/...` that unifies the former operational backbone (`core-v1`) and agent-native line (`core-v2`). Historical specs are preserved under [archive/v1/](archive/v1/) and [archive/v2/](archive/v2/).

## Structure

- [openapi/gmp-core-v3.yaml](openapi/gmp-core-v3.yaml): Unified REST API (sessions, registry, policy, runs, availability, events, capability tokens, negotiation, durable execution, memory, accounting, evals, coordination, sandbox, supervision).
- [profiles/core-v3.json](profiles/core-v3.json): Conformance profile (`requiredOperations`, `requiredSchemas`, `reproducibilityTiers`, `complianceChecks`, `extensionPolicy`).
- [schemas/common/](schemas/common/): Shared object schemas.
- [schemas/events/](schemas/events/): Event taxonomy, [event-envelope-base.schema.json](schemas/events/event-envelope-base.schema.json), discriminated [event-envelope.schema.json](schemas/events/event-envelope.schema.json), and specializations.
- [fixtures/v3/](fixtures/v3/): Machine-validated example payloads for the validator.
- [v3-design-notes.md](v3-design-notes.md): Unification decisions (identity, runs, errors, events).
- [v3-release-governance.md](v3-release-governance.md): Stub release and GA policy (expand with real thresholds later).

## v3 surface (conceptual)

1. **Identity**: `establishSession`, capability token mint/revoke/audit.
2. **Capability registry**: list, register, get.
3. **Policy**: `evaluatePolicy`.
4. **Runs**: `planRun`, `submitRun`, `getRun`, `cancelRun`, `retryRun`, `pauseRun`, `resumeRun`, `listRunCheckpoints`.
5. **Availability**: list targets.
6. **Events**: `appendEvent`, `listEvents` (journal lineage as `journal.*` types, reasoning and tool calls in the same stream).
7. **Memory, accounting, evals, agents, actions, supervision**: unchanged intent from v2 paths, now under `/v3/...`.

## What changed from v1 / v2

| Topic | v1 | v2 | v3 |
| --- | --- | --- | --- |
| Base path | `/v1/...` | `/v2/...` | `/v3/...` only |
| Token exchange | `exchangeToken` | (session implied) | `establishSession` |
| Journal vs reasoning | Journal API only | Separate experimental reasoning listing | Single `/v3/events` API |
| Errors | `ErrorResponse` | `StructuredError` | `StructuredError` everywhere |
| Profiles | `core-v1.json` | `core-v2.json` | `core-v3.json` (see archive for prior) |

## Versioning rules

- APIs are path-versioned using `/v3/...`.
- Schemas carry `$id` and semantic meaning in profile metadata.
- Minor releases: additive optional fields and new endpoints only.
- Breaking changes: new major path (for example `/v4/...`) and migration notes.

## Compatibility policy

A deployment is **core-v3** compatible when:

1. OpenAPI validates with no unresolved references.
2. Every `requiredOperations` entry in [core-v3.json](profiles/core-v3.json) is implemented.
3. Every `requiredSchemas` file exists and validates.
4. Failure taxonomy stays consistent across run, journal, and event payloads.
5. Fixture validation passes: `make validate-v3-contracts`.

## Extension policy

- Extensions must not alter core semantics of required operations.
- Use `x-gmp-*` custom fields or routes under `/v3/experimental/*` (see [v3-design-notes.md](v3-design-notes.md)).
- Core compatibility tests must pass with extensions enabled.

## Release process

1. Update schemas and OpenAPI.
2. Validate OpenAPI (for example `@redocly/cli lint openapi/gmp-core-v3.yaml`).
3. Run `make validate-v3-contracts`.
4. Update [v3-release-governance.md](v3-release-governance.md) release notes section when cutting a release.
5. Publish release notes with contract impact.

## Acceptance checklist

- [ ] `gmp-core-v3.yaml` validates cleanly.
- [ ] All `$ref` paths resolve.
- [ ] `core-v3.json` lists all mandatory operations and schema dependencies.
- [ ] Examples exist for session → capability token → plan → submit → event append flow.

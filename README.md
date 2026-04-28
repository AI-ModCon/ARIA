# GMP Contracts

This directory defines the Genesis Mission Platform (GMP) v1 contract baseline.

## Structure

- `openapi/gmp-core-v1.yaml`: Primary REST API contract for core services.
- `schemas/common/`: Canonical shared object schemas.
- `schemas/events/`: Event envelope and taxonomy schemas.
- `profiles/core-v1.json`: Core conformance requirements and reproducibility tiers.

## Contract Coverage

The v1 baseline includes the following service domains:

- Identity/Trust (token exchange and delegation claims)
- Capability/Artifact/Data Registry
- Run Control (submit, status, cancel, retry)
- Policy Decisions
- Availability and readiness
- Journal/Provenance events
- Conformance and reproducibility tiering

## Versioning Rules

- APIs are path-versioned using `/v1/...`.
- Schemas use semantic version metadata in file content and profile metadata.
- Minor releases are additive only:
  - New optional fields allowed.
  - New endpoints allowed.
  - Existing required fields cannot be removed or newly required in minor versions.
- Breaking changes require a new major line (for example, `v2`) and migration notes.

## Compatibility Policy

A deployment is `core-v1` compatible only if all of the following pass:

1. OpenAPI validates with no unresolved references.
2. Required operations listed in `profiles/core-v1.json` are present.
3. Required schemas are present and referenced by API operations.
4. Failure taxonomy is consistently represented in run and journal contracts.
5. Example payloads validate against corresponding schemas.

## Extension Policy

- Extensions are allowed only when they do not alter core semantics.
- Use one of these extension patterns:
  - `x-gmp-*` custom fields in existing contracts.
  - `/v1/extensions/*` route namespace for non-core APIs.
- Core compatibility tests must continue to pass with extensions enabled.

## Release Process

1. Update schemas and OpenAPI specs.
2. Validate OpenAPI and JSON Schemas.
3. Ensure profile checks pass (`requiredOperations`, `requiredSchemas`, taxonomy checks).
4. Add or update example payloads for changed contracts.
5. Publish release notes with compatibility impact.

## Acceptance Checklist

- [ ] `gmp-core-v1.yaml` validates cleanly.
- [ ] All `$ref` paths resolve.
- [ ] Core objects (`Capability`, `Run`, `Artifact`, `DatasetRef`, `PolicyDecision`, `JournalEvent`, `ExecutionContext`) are canonical and reused.
- [ ] Failure taxonomy is shared by run and journal/event contracts.
- [ ] `profiles/core-v1.json` lists all mandatory operations and schema dependencies.
- [ ] Examples exist for discovery -> policy -> run -> journal flow.

## Example Flow Payloads

### 1) Capability registration (request snippet)

```json
{
  "capabilityId": "cap.simulation.kolmogorov.v1",
  "name": "Kolmogorov Simulation",
  "version": "1.0.0",
  "profile": "core",
  "executionContext": {
    "configHash": "a3e5d2571606f4f8a13f0f248f54f4e35f3e7f56d76d5f7c7a82f5f6567a0f84",
    "environmentHash": "c3f7af31a1722ea9639f99d75cf4228fa30f7ec398bd6111f0cc4dbf19773621",
    "seedList": [42],
    "dataVersion": "2026.03"
  },
  "artifact": {
    "artifactId": "artifact.kolmogorov.v1",
    "kind": "workflow",
    "uri": "https://registry.example/artifacts/kolmogorov-v1",
    "digest": "sha256:3f7f950ecf6ec26bca1eef9ec0ee9f71329f8d5cd32df1df9223e95a3f5bc48f",
    "lockfileUri": "https://registry.example/artifacts/kolmogorov-v1/lockfile",
    "invocationManifestUri": "https://registry.example/artifacts/kolmogorov-v1/invocation",
    "datasetRefs": [],
    "smokeTestStatus": "passed"
  },
  "status": "smoke_test_passed",
  "reproducibilityTier": "tier2_smoke_tested"
}
```

### 2) Policy decision (response snippet)

```json
{
  "decision": "conditional",
  "rationaleCode": "requires_training",
  "obligations": [
    { "type": "human_approval", "value": "required" }
  ],
  "providerEnforcement": "required"
}
```

### 3) Run submission (response snippet)

```json
{
  "runId": "run_01JYV6HEP9V0M2B8Q62J4AYM4D",
  "capabilityId": "cap.simulation.kolmogorov.v1",
  "status": "queued",
  "submittedAt": "2026-04-28T18:00:00Z",
  "executionContext": {
    "configHash": "a3e5d2571606f4f8a13f0f248f54f4e35f3e7f56d76d5f7c7a82f5f6567a0f84",
    "environmentHash": "c3f7af31a1722ea9639f99d75cf4228fa30f7ec398bd6111f0cc4dbf19773621",
    "seedList": [42],
    "dataVersion": "2026.03"
  },
  "failureClass": "F0_NONE"
}
```

### 4) Journal event (request snippet)

```json
{
  "eventId": "evt_01JYV6P3W3JQW8Y2KJ8T7TBVAA",
  "runId": "run_01JYV6HEP9V0M2B8Q62J4AYM4D",
  "eventType": "run.completed",
  "timestamp": "2026-04-28T18:04:12Z",
  "failureClass": "F0_NONE",
  "lineageRefs": ["https://provenance.example/lineage/run_01JYV6HEP9V0M2B8Q62J4AYM4D"],
  "details": {
    "durationSeconds": 252
  }
}
```

# GMP v3 release governance (stub)

This stub replaces archived [v2-release-governance.md](archive/v2/v2-release-governance.md) for the unified **core-v3** line. Concrete numeric targets and calendar dates are TBD.

## Release cadence

- **Contract patch**: additive JSON Schema and optional OpenAPI fields only; profile `version` patch bump.
- **Contract minor**: new optional operations or new experimental routes under `/v3/experimental/*`; profile minor bump with release notes.
- **Contract major**: breaking semantics or removal of required operations → new major API path (for example `/v4/...`) and new profile id.

## GA exit criteria (checklist)

Placeholders for implementation and CI to enforce over time:

1. OpenAPI [gmp-core-v3.yaml](openapi/gmp-core-v3.yaml) validates with zero unresolved `$ref`s.
2. [core-v3.json](profiles/core-v3.json) `requiredOperations` and `requiredSchemas` resolve and match the spec.
3. Fixture suite under [fixtures/v3/](fixtures/v3/) validates via `make validate-v3-contracts`.
4. Durable execution: pause/resume/checkpoint fixtures demonstrate replay-safe identifiers (expand fixture coverage beyond current stub).
5. Sandbox: propose → approve → apply → rollback path covered by fixtures.
6. Supervision: queue + intervention fixtures align with production scenarios.
7. Reasoning trace: event stream query returns correlated `eventId` / `correlationId` chains (documented consumer contract).

## Experimental route graduation

- New behavior starts under `/v3/experimental/...` or as optional schema fields with `x-gmp-` prefix.
- Graduation to core requires: profile update, OpenAPI path promotion (if applicable), fixtures, and at least one release note calling out the promoted surface.
- Deprecated experimental routes remain documented for one minor release before removal.

## Version metadata

- OpenAPI `info.version` tracks the API description revision.
- Profile `version` in `core-v3.json` tracks the conformance bundle revision; keep them aligned in release notes when both change.

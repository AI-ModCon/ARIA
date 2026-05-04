# GMP Contracts (core-v3)

This directory defines the **Genesis Mission Platform (GMP) core-v3** contract baseline: one OpenAPI surface under `/v3/...` that unifies the former operational backbone (`core-v1`) and agent-native line (`core-v2`). Historical specs are preserved under [archive/v1/](archive/v1/) and [archive/v2/](archive/v2/).

## Spine charter

**Core v3 is intentionally a spine**, not a single universal integration contract for every scientific workflow surface. Scope: an **agent-first, AI-native** control plane that **interoperates across the enterprise** via stable identity, policy, governed execution, provenance-style events, and capability registration—not via encoding full data meshes, leaderboard products, OCR pipelines, or facility-specific transports inside this OpenAPI document alone.

What the spine **does** guarantee (implementations must conform to [profiles/core-v3.json](profiles/core-v3.json)):

- Session bootstrap and **scoped, revocable** capability delegation (`establishSession`, capability tokens).
- **Capability registry** and **single Run** abstraction with execution context hashes, optional **plan linkage** (opaque reference + digest to companion plan artifacts).
- **Policy evaluation**, **sandboxed actuation**, **supervision**, and a **unified event stream** for audit and reasoning tooling.
- **Durable execution** (pause, resume, checkpoints) and operational **budget / routing hints** adjacent to accounting.

What the spine **does not** require (belongs to **companion schemas**, capabilities, MCP servers, deployment planes, or program-specific APIs unless adopted into an optional profile):

- Full Globus/catalog/data-plane operation sets, multimodal ingestion, OCR stacks, leaderboard portals as core paths.
- Typed multi-step **campaign graphs** themselves (use [companion/](companion/README.md) `CampaignPlan` and link from `planRef` / `planDigest`).
- Low-latency streaming channels (document in design notes / edge deployments; correlate with existing `correlationId` / `runId`).

Demand-side analyses that score “gaps versus v3” should be read with this charter: gaps are often **outside spine GA** while still **tracked** in [GAP_DISPOSITION_REGISTER.md](GAP_DISPOSITION_REGISTER.md).

## Structure

- [openapi/gmp-core-v3.yaml](openapi/gmp-core-v3.yaml): Unified REST API (sessions, registry, policy, runs, availability, events, capability tokens, negotiation, durable execution, memory, accounting, evals, coordination, sandbox, supervision).
- [profiles/core-v3.json](profiles/core-v3.json): Conformance profile (`requiredOperations`, `requiredSchemas`, `reproducibilityTiers`, `complianceChecks`, `extensionPolicy`).
- [schemas/common/](schemas/common/): Shared object schemas.
- [schemas/events/](schemas/events/): Event taxonomy, [event-envelope-base.schema.json](schemas/events/event-envelope-base.schema.json), discriminated [event-envelope.schema.json](schemas/events/event-envelope.schema.json), and specializations.
- [fixtures/v3/](fixtures/v3/): Machine-validated example payloads for the validator.
- [companion/](companion/README.md): Optional interoperability schemas (`CampaignPlan`, `DataMovementIntent`, `EvalPublication`) for enterprises that adopt the **core-v3-companion** bundle (see [profiles/core-v3-companion.json](profiles/core-v3-companion.json)).
- [GAP_DISPOSITION_REGISTER.md](GAP_DISPOSITION_REGISTER.md): Maps consolidated workflow themes to spine vs companion vs capability disposition.
- [v3-design-notes.md](v3-design-notes.md): Unification decisions (identity, runs, errors, events).
- [v3-release-governance.md](v3-release-governance.md): Stub release and GA policy (expand with real thresholds later).
- [archive/v1/](archive/v1/) and [archive/v2/](archive/v2/): Historical OpenAPI, profiles, fixtures, and v2 migration/governance docs (not part of the active conformance line).

## v3 API surface (aligned with OpenAPI tags)

All paths are under `/v3/...`. Operation IDs below match [profiles/core-v3.json](profiles/core-v3.json) `requiredOperations` and [openapi/gmp-core-v3.yaml](openapi/gmp-core-v3.yaml).

| Tag | Operations |
| --- | --- |
| **IdentityTrust** | `establishSession` |
| **IdentityTrustV2** | `mintCapabilityToken`, `revokeCapabilityToken`, `getCapabilityTokenAudit` |
| **CapabilityRegistry** | `listCapabilities`, `registerCapability`, `getCapability` |
| **PolicyDecision** | `evaluatePolicy` |
| **RunControl** | `submitRun`, `getRun`, `cancelRun`, `retryRun` |
| **Negotiation** | `planRun` |
| **DurableExecution** | `pauseRun`, `resumeRun`, `listRunCheckpoints` |
| **Availability** | `listTargetAvailability` |
| **Memory** | `writeMemoryRecord`, `queryMemoryRecords`, `summarizeMemoryRecords`, `forgetMemoryRecords` |
| **Accounting** | `getTaskUsage`, `allocateBudget`, `enforceBudget` |
| **ReasoningObservability** | `runEval`, `getEvalResult` |
| **AgentCoordination** | `sendAgentMessage`, `handoffAgentTask`, `resolveAgentConsensus` |
| **SandboxActuation** | `proposeAction`, `approveAction`, `applyAction`, `rollbackAction` |
| **Supervision** | `listSupervisionQueue`, `recordIntervention`, `listDivergenceAlerts` |
| **EventsProvenance** | `appendEvent`, `listEvents` (unified stream: journal-style `journal.*`, reasoning, tool calls) |

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
5. Fixture validation passes: `make validate-v3-contracts` (from repo root; runs [scripts/validate_v3_contracts.py](../scripts/validate_v3_contracts.py)).
6. Profile `complianceChecks` in [core-v3.json](profiles/core-v3.json) (identity revocation, idempotency, durable execution, memory/budget policy, reasoning trace, sandbox gates, supervision) are satisfied by the deployment’s behavior and tests—expand coverage as implementations land.

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

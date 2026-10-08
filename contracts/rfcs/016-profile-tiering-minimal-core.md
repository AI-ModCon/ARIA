# RFC 016: Profile tiering — minimal core and optional modules

## Problem

[`profiles/core-v3.json`](../profiles/core-v3.json) makes all 38 operations mandatory for any
conformant deployment. A site gateway that faithfully implements identity, runs, events, and
policy must also serve `summarizeMemoryRecords`, `resolveAgentConsensus`, `rollbackAction`,
and `listDivergenceAlerts` — or be "conformant" only via stub theater, which destroys the
profile's signal value. Several `complianceChecks` (`memory_policy_enforced`,
`budget_policy_enforced`, `sandbox_gate_apply_rollback_validated`,
`supervision_workflows_validated`) presuppose subsystems a deployment may legitimately not
host. An ARIA deployment is an assembly; the profile should say which parts of the assembly
a given endpoint provides. RFC 015 asks whether HTTP 501 stubs count as conformant; tiering
answers that structurally — a deployment claims only the modules it implements.

## Proposal

- Add a **`minimal-core-v3` profile**: identity, registry, policy, runs, events only —
  `establishSession`, `mintCapabilityToken`, `revokeCapabilityToken`,
  `getCapabilityTokenAudit`, `listCapabilities`, `registerCapability`, `getCapability`,
  `evaluatePolicy`, `submitRun`, `getRun`, `cancelRun`, `retryRun`, `appendEvent`,
  `listEvents` (14 of 38).
- Partition the remaining 24 operations into **named optional modules**, each a profile
  fragment using the `extendsProfileId` mechanism already present in
  [`profiles/core-v3-companion.json`](../profiles/core-v3-companion.json):
  `durable-execution` (`planRun`, `pauseRun`, `resumeRun`, `listRunCheckpoints`),
  `memory` (4 ops), `accounting` (`getTaskUsage`, `allocateBudget`, `enforceBudget`),
  `evals` (2 ops), `coordination` (`sendAgentMessage`, `handoffAgentTask`, and
  `resolveAgentConsensus` marked experimental — see below and RFC 021),
  `sandbox` (4 action-gate ops), `supervision` (`listSupervisionQueue`,
  `recordIntervention`, and `listDivergenceAlerts` marked experimental),
  `availability` (`listTargetAvailability`).

### Experimental operations within modules

Per RFC 021, `resolveAgentConsensus` and `listDivergenceAlerts` are listed in their
modules under a distinct `experimentalOperations` key, not `requiredOperations`. A
deployment claiming the `coordination` or `supervision` module implements that module's
`requiredOperations` only; experimental operations are never required for any module
claim or conformance level, and graduate per the RFC 021 bar.

### Compliance-check partition

Module profiles carry their own `requiredSchemas` and `complianceChecks`. The partition
of today's `core-v3.json` `complianceChecks` is:

- **Stay on `minimal-core-v3`**: `openapi_valid`, `all_refs_resolve`,
  `required_operations_present`, `failure_taxonomy_consistent`,
  `schema_examples_present`, `identity_revocation_enforced`,
  `idempotency_required_on_mutations`.
- **Move with their modules**: `durable_execution_resume_replay_safe` →
  `durable-execution`; `memory_policy_enforced` → `memory`; `budget_policy_enforced` →
  `accounting`; `sandbox_gate_apply_rollback_validated` → `sandbox`;
  `supervision_workflows_validated` → `supervision`; `reasoning_trace_queryable` →
  `evals`. (`reasoning_trace_queryable` is not implied by `appendEvent` / `listEvents`
  alone — it requires reasoning-node events to exist and be retrievable by correlation,
  which a deployment with no reasoning workloads cannot evidence; it therefore moves off
  the floor to the module whose operations produce that evidence.)

### Conformance levels

Levels are module bundles: **C0** = minimal core; **C1** = C0 + `durable-execution` +
`availability`; **C2** = C1 + `accounting` + `sandbox`; **C3** = C2 + `supervision` +
`evals`; **C4** = C3 + `coordination` + `memory` — that is, **every module's
`requiredOperations`, excluding experimental operations**. A legacy `core-v3` deployment
is a C4 deployment plus the two experimental operations `core-v3.json` obliged it to
serve (typically as stubs); `core-v3` remains a valid claimable profile for continuity,
and C4 is the recommended successor claim.

### Federation profile

Add a **`federation-v3` profile** = minimal core + three cross-trust-domain constraints,
each stated so a conformance kit can fail it:

- `payloadSerialization`: every cross-domain `AgentMessage.payload`, handoff-referenced
  artefact, and action argument object MUST validate as JSON; a fixture whose payload
  contains a serialized-object blob (e.g. base64 pickle) MUST be rejected by the
  receiving deployment.
- `delegationChainMaterialized`: every capability token presented across a trust-domain
  boundary MUST carry `delegation.delegationChain` with one entry per delegation hop from
  the human principal to the presenting workload; a token whose chain omits an
  intermediate hop MUST be refused at use time.
- `revocationCheckPerHop`: at every use of a capability token, each delegation hop in the
  chain MUST be re-checked against revocation state; a fixture presenting a token whose
  intermediate delegator has been revoked MUST be denied, even if the leaf token itself
  is unexpired and unrevoked.

### Versioning

New profile ids are additive, so tiered profiles ship within v3 ("contract minor" per
[`v3-release-governance.md`](../v3-release-governance.md)); `core-v3.json` is left
intact. Shrinking the flagship profile's `requiredOperations` is a contract-major action
and should be **the driver for the v4 profile turn**.

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §5.1: no single
framework (Academy, LangGraph, Ray) implements the 38-operation surface, and none should.

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
  `evals` (2 ops), `coordination` (`sendAgentMessage`, `handoffAgentTask`,
  `resolveAgentConsensus` — see RFC 021), `sandbox` (4 action-gate ops),
  `supervision` (3 ops), `availability` (`listTargetAvailability`).
- Move each module's `requiredSchemas` and `complianceChecks` into the module profile
  (e.g. `memory_policy_enforced` lives in `memory`, not minimal core).
- Define **conformance levels** as module bundles: **C0** = minimal core; **C1** = C0 +
  `durable-execution` + `availability`; **C2** = C1 + `accounting` + `sandbox`;
  **C3** = C2 + `supervision` + `evals`; **C4** = all modules (today's `core-v3`).
- Add a **`federation-v3` profile** = minimal core + cross-trust-domain constraints
  (JSON-only payload serialization, materialized `IdentityClaims.delegationChain`,
  revocation checks on every hop).
- Versioning: new profile ids are additive, so tiered profiles ship within v3 ("contract
  minor" per [`v3-release-governance.md`](../v3-release-governance.md)); `core-v3` remains
  valid as the C4 bundle. Shrinking the flagship profile's `requiredOperations` is a
  contract-major action and should be **the driver for the v4 profile turn**.

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §5.1: no single
framework (Academy, LangGraph, Ray) implements the 38-operation surface, and none should.

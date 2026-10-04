# federation-v4: tiered conformance levels (draft)

Companion prose for [federation-v4.json](federation-v4.json). The profile extends
[core-v4-minimal.json](core-v4-minimal.json) with cross-trust-domain constraints
(JSON-only payload serialization, materialized `IdentityClaims.delegationChain`,
revocation check on every delegation hop) and defines five conformance levels. Each
level is a bundle of named modules from [core-v4-modules.json](core-v4-modules.json)
plus an **evidence class** stating how the conformance kit was passed — so no site can
claim a live tier from reference-only passes.

**C0 — minimal core, reference evidence.** The deployment implements the 14
minimal-core operations (identity, registry, policy, runs, events) and passes the
conformance kit against reference fixtures. This is the entry tier for a new
implementation or a university sandbox; nothing live is claimed.

**C1 — locally governed, local-live evidence.** Adds `durable-execution` and
`availability`. Evidence is gathered against a live local control plane: duplicate
launch prevented, replay reconstructs terminal state, revocation blocks subsequent
action. This is the tier a single-institution deployment needs before touching any
facility resource.

**C2 — facility-attached, scheduler-live evidence.** Adds `accounting` and `sandbox`.
Evidence is gathered against a real scheduler via the site gateway: one Run maps to one
scheduler job, restart converges with no orphaned jobs (see the ExecutionAttempt
companion schema), budgets crosswalk to facility allocation units, and consequential
actions pass through propose/approve/apply/rollback gates.

**C3 — federated, fleet-live evidence.** Adds `supervision` and `evals`. Evidence spans
at least two administrative domains: delegated authority attenuates across the handoff
chain, an independent evaluator catches a seeded bad result, and supervision queues and
interventions operate across sites.

**C4 — production, cross-org-live evidence.** Every module's `requiredOperations`,
including `coordination` and `memory`, and excluding experimental operations. A legacy
`core-v3` deployment is a C4 deployment plus the two experimental operations
`core-v3.json` obliged it to serve (typically as stubs). Evidence includes cross-organization campaigns with complete provenance,
demonstrated revocation and disaster recovery, and a security review against the exact
release candidate. In v4, C4 is the ceiling, not the floor.

Experimental operations (`resolveAgentConsensus`, `listDivergenceAlerts`) are not
required at any level; they graduate per the release-governance process once two
independent interoperating implementations exist (RFC 021).

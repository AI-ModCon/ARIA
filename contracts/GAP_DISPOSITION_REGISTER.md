# Gap disposition register — Core v3 as spine

**Purpose:** Consolidated workflow analyses (see `Simulation Results/Workflow_Requirements_Synthesis.md` and `Simulation Results/Workflow Requirements vs v3.md`) list many “gaps” when scored against schemas and operations alone. Core v3 is a **spine**; items below are dispositioned into **what belongs in spine**, **companion schemas**, **capability/implementations**, **experimental**, or **out of spine GA**.

**Legend**

| Disposition | Meaning |
| ----------- | ------- |
| `spine_patch` | Additive change to schemas in `contracts/schemas/` and/or documented OpenAPI semantics; ships with fixtures and profile bumps. |
| `spine_experimental` | `x-gmp-*` fields or `/v3/experimental/*` routes per [v3-release-governance.md](v3-release-governance.md) before graduation. |
| `companion_spec` | JSON Schema under [companion/](companion/README.md); linked from Runs via refs/digests, not duplicated as core REST surface. |
| `capability_profile` | Implemented as advertised **capabilities**, MCP servers, or site adapters; spine records events and applies policy/sandbox only. |
| `out_of_scope_core` | No core-v3 commitment; enterprise or program owns specifications elsewhere. |

| Gap ID | Theme | Related CRs (from Workflow Requirements vs v3) | Disposition | Home / artefact |
| ------ | ----- | ---------------------------------------------- | ----------- | ----------------- |
| GAP-001 | Typed multi-step plan / DAG (`planRun` too shallow vs graph builders) | `CR-UX-3`, `CR-COG-2` | `companion_spec` | [companion/schemas/campaign-plan.schema.json](companion/schemas/campaign-plan.schema.json); spine: `planRef`, `planDigest`, `planId` on Run |
| GAP-002 | Uncertainty / confidence (UQ) propagation | `CR-UX-5`, `CR-GOV-15` | `spine_patch` | [schemas/common/uncertainty.schema.json](schemas/common/uncertainty.schema.json) on `eval-result`, reasoning payload |
| GAP-003 | Streaming / low-latency path | `CR-UX-7`, `CR-RUN-9`, `CR-RUN-16`, `CR-DATA-13`, `CR-INFRA-12` | `spine_experimental` + `capability_profile` | Edge channels and facility adapters; correlate with `runId` / `correlationId` (see [v3-design-notes.md](v3-design-notes.md)) |
| GAP-004 | Cross-facility data movement | `CR-DATA-2`, `CR-INFRA-11` | `companion_spec` + `capability_profile` | [companion/schemas/data-movement-intent.schema.json](companion/schemas/data-movement-intent.schema.json); movers as capabilities |
| GAP-005 | Public DOE-science leaderboard / release path | `CR-GOV-10`, `CR-GOV-19` | `companion_spec` | [companion/schemas/eval-publication.schema.json](companion/schemas/eval-publication.schema.json); spine keeps `runEval` / `getEvalResult` |
| GAP-006 | AI vs non-AI comparator runs | `CR-GOV-12` | `companion_spec` | Express as `suiteId`/metadata conventions in `CampaignPlan` or extension of `eval-publication`; optionally capability-only |
| GAP-007 | Mid-run classification / risk escalation | `CR-GOV-8` | `spine_patch` | Event `classification.shift` plus optional labels on [`workflow-state.schema.json`](schemas/common/workflow-state.schema.json) |
| GAP-008 | Separate skill/card type registry | `CR-REG-9` | `capability_profile` | Use `capability` + domain tags + companion metadata; spine does not mandate six-way card enums |
| GAP-009 | MCP gallery approval semantics | `CR-REG-2` | `capability_profile` | Registry implementation; spine exposes `capability.status`—extend deployments with promoted approval workflow if needed |
| GAP-010 | Capability licensing / IPFP metadata | `CR-REG-6` | `spine_patch` | Optional `accessPrerequisites` on [capability.schema.json](schemas/common/capability.schema.json) (parity with datasets) |
| GAP-011 | Federated training wire protocol | `CR-RUN-12` | `out_of_scope_core` unless mandated | Dedicated program companion or experimental profile—not `requiredOperations` in core-v3 GA |
| GAP-012 | Aggregate “provenance capsule” document | `CR-GOV-4` | `capability_profile` | Materialized read model over events + run + checkpoints; spine supplies components only |
| GAP-013 | µE GPU power / energy telemetry | `CR-RUN-14` | `out_of_scope_core` | OpenTelemetry / site metrics; optional `journal.*` payloads if deployments choose |

**Owners and priorities**

Program leadership should assign `owner`, `priority` (P0–P3), and target milestone per row; this file intentionally omits placeholders so teams can paste their tracker IDs.

**Related**

- [README.md](README.md) Spine charter and structure pointers
- Optional bundle: [profiles/core-v3-companion.json](profiles/core-v3-companion.json)

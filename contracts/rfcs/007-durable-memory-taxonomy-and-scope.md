# RFC-007: Durable Memory Taxonomy & Scope

- **Status:** Draft
- **Target:** `contracts/` — new schemas under `schemas/common/`, new ops in
  `openapi/gmp-core-v3.yaml`, Memory tag in `README.md`
- **Domain:** Memory
- **Priority:** P2
- **Author:** nkkchem
- **Origin:** [ARIAPlatform](https://github.com/brettin/ARIAPlatform_v0) alignment work
- **Supersedes/extends:** the current single-record Memory surface

## Summary

ARIA's Memory domain today specifies **one** durable surface — a generic
`MemoryRecord` with a nominal `kind` label — plus four ops
(write/query/summarize/forget). In practice only **episodic** memory (raw run
history + `summary` compaction) is meaningfully specified. A self-improving,
closed-loop scientific platform needs more. This RFC adds four durable memory
surfaces onto the existing one, resolves the sharing-scope ambiguity, and marks
working/scratch memory explicitly out of scope. Every addition is stated as a
delta on the current contract, with an explicit rationale for **why the existing
surface is insufficient**.

## 1. Current state (what the contract has today)

| Artifact | Path | Content |
|---|---|---|
| Ops | `contracts/openapi/gmp-core-v3.yaml` (L470–555) | `writeMemoryRecord`, `queryMemoryRecords`, `summarizeMemoryRecords`, `forgetMemoryRecords` |
| Record | `contracts/schemas/common/memory-record.schema.json` | `memoryId, agentId, kind, content, createdAt, policy` (+opt `sharing`); `kind ∈ {episodic, semantic, entity, summary}` |
| Policy | `contracts/schemas/common/memory-policy.schema.json` | `retentionSeconds, summarizationMode, sharingMode∈{private,tenant,cross_agent}, privacyTags` |
| Sharing | `contracts/schemas/common/memory-sharing.schema.json` | `ownerAgentId, sharedWith[], accessLevel∈{read,read_write,summary_only}` |

The `MemoryRecord` is a single free-text blob differentiated only by a `kind`
string. `episodic` (append raw run history) and `summary` (compaction) are the
only kinds the ops actually exercise; `semantic` and `entity` are labels with no
distinct structure, lifecycle, or access rules.

## 2. Why the existing surface is not enough (the distinction)

The core problem: **one schema cannot express four different memory *contracts*.**
Each memory type has a different shape, different write/read semantics, a
different lifecycle, and a different auth/immutability requirement. Collapsing
them into `content: string + kind: enum` erases exactly the properties that make
each type useful. Concretely:

| Question the loop must answer | Memory type that answers it | Can today's `MemoryRecord` answer it? |
|---|---|---|
| *"What happened on run X?"* | **Episodic** (have) | ✅ yes — this is the one it does |
| *"What do we now believe is true, and how sure are we?"* | **Semantic** (fact + confidence + evidence + validity) | ❌ no — no confidence, evidence, validity, or supersession; a belief can't be revised, only appended as more text |
| *"What sequence of steps actually worked, so I can run it again?"* | **Procedural** (recipe + steps + replay) | ❌ no — no steps, no capability refs, no replay op; a blob of text is not executable |
| *"Why was this decision made, and can I prove it wasn't tampered with?"* | **Provenance/Audit** (hash-chained, signed, immutable) | ❌ no — records are mutable/soft-deletable, no hash chain, no signature |
| *"What may agent B on this campaign see from agent A?"* | **Shared/collective** (scoped) | ⚠️ ambiguous — two overlapping mechanisms, `cross_agent` is unbounded, nothing enforced |

**The self-improvement argument.** A closed loop improves by (1) *recording* what
happened → episodic; (2) *generalizing* it into beliefs → semantic; (3)
*crystallizing* winning strategies into reusable recipes → procedural; and (4)
*justifying* each autonomous action so a human/auditor can trust it → provenance.
Today only step (1) is real. Steps (2)–(4) either can't be expressed or can't be
trusted. That is the gap this RFC closes.

**Design stance:** keep `MemoryRecord`/episodic exactly as-is (no breaking
change) and add the other surfaces *alongside* it, each with its own schema and
ops, all tied together by one shared `scope` primitive (§3).

## 3. Shared scope model (the primitive every surface reuses)

New `memory-scope.schema.json`: `level ∈ {agent, campaign, platform}` + `agentId`
(when agent), `campaignId` (when campaign), `tenantId` (always). Every new
surface references it. Access is enforced at read time against the caller's
capability token (IdentityTrust `establishSession`); cross-scope reads require an
explicit grant claim.

- **agent** — private to one agent (default; = today's `private`).
- **campaign** — shared across agents cooperating on one project/run-group
  (the missing middle; a bounded form of today's unbounded `cross_agent`).
- **platform** — tenant-wide curated knowledge, promotion-gated.

## 4. Semantic memory — beliefs/facts (new)

**Why (vs. existing):** episodic answers "what happened"; semantic answers "what
is true and how sure." Needs `confidence`, `evidence` links, a validity window,
and **supersession** so a belief can be *revised*, not just re-appended as text.

- **Ops:** `writeSemanticFact` `POST /v3/memory/semantic`;
  `querySemanticFacts` `POST /v3/memory/semantic/query` (filter subject/predicate/
  tag/`minConfidence`/validity-at-time); `promoteSemanticFact` (policy-gated
  promotion of a `summarize` output to campaign/platform).
- **Schema `semantic-fact.schema.json`:** `factId, scope, proposition,
  {subject,predicate,object}?, confidence[0..1], evidence[]{type,id},
  validFrom, validUntil?, supersedes[], createdAt, policy`.
- **Auth:** write = own agent; promote needs `memory:promote` + PolicyDecision;
  reads per §3.
- **Distinction:** supersession = belief revision (writing with `supersedes`
  closes the prior fact's validity, preserving history) — impossible with the
  current append-only blob.

## 5. Procedural memory — replayable recipes (new, highest priority)

**Why (vs. existing):** this is the actual engine of *self-improving*. Episodic
recalls, semantic generalizes, but only procedural lets the loop **repeat a
winning strategy**. A text blob is not executable; a recipe with typed steps is.

- **Ops:** `writeProcedure` `POST /v3/memory/procedures` (server assigns
  `procedureId`+immutable `version`); `queryProcedures` (by goal/tag/
  `minSuccessRate`/required capabilities); `getProcedure` `GET .../{id}`;
  `replayProcedure` `POST .../{id}/replay`.
- **Replay is governed, not direct:** it materializes a RunControl plan from the
  steps and returns a `runId`, so replay re-passes policy/negotiation/budget
  gates and **cannot escalate privilege**. Run completion feeds
  `successCount/attemptCount` back via EventsProvenance (evidence-backed
  reliability, not self-asserted).
- **Schema `procedure.schema.json`:** `procedureId, version, scope, goal,
  preconditions[], steps[]{order,capabilityRef,operation,parameters,expects},
  successCriteria[], successCount, attemptCount, derivedFrom[runRef], createdAt,
  policy`.
- **Auth:** write/version = own agent; replay requires the caller to already
  hold tokens for every `capabilityRef`; promotion gated as §4.

## 6. Shared/collective memory — SCOPE DECISION

> **⚠️ DECISION REQUIRED.** Today's `sharingMode ∈ {private,tenant,cross_agent}`
> and `sharing.sharedWith[]` overlap, `cross_agent` is unbounded, and nothing is
> enforced. Pick one model.

**Recommendation:** adopt the 3-level `scope` (§3), replacing the overlapping
pair. Per-agent alone is too isolated for multi-agent campaigns; platform-only
sharing leaks across unrelated projects (a DOE privacy hazard); **per-campaign**
is the missing middle bounding collaboration to the unit of scientific teamwork.

**Auth boundary on cross-agent reads:** agent → owner only; campaign → any agent
whose token carries the matching `campaignId` claim (write needs membership +
`memory:write`); platform → any tenant agent reads, writes only via promotion.
Denied cross-scope reads are logged to provenance (§7).

**Fallback if unratified:** keep `agent`-only as the conformance floor; make
`campaign`/`platform` an OPTIONAL profile extension; deprecate `sharedWith[]`
(kept for back-compat, superseded by `scope`).

## 7. Provenance/audit memory — tamper-evident "why" (new)

**Why (vs. existing & vs. the events journal):** EventsProvenance is an
*operational* stream (that something happened). Provenance/audit memory is a
durable, **immutable, verifiable** record of *why* a decision was made — required
to trust an autonomous agent in a DOE setting. Current records are mutable and
soft-deletable, with no hash chain or signature: not defensible in an audit.

- **Ops:** `appendProvenanceRecord` `POST /v3/memory/provenance` (append-only;
  server computes `recordHash` over payload+`previousRecordHash`, stores
  `signature`/`signer`); `queryProvenanceRecords`; `verifyProvenanceChain`
  (recompute chain + validate signatures, report first break).
- **Schema `provenance-record.schema.json`:** `recordId, scope, decision,
  rationale, inputs[]{type,id}, policyVerdicts[]{policyId,verdict},
  approvals[]{approver,at}, recordHash, previousRecordHash?, signature, signer,
  createdAt`.
- **Auth:** append needs `provenance:write` (platform/executor identity); read
  needs `audit:read` scoped to run/campaign. **No update/delete for anyone** —
  explicitly exempt from the Memory `forget` op (forgetting would defeat audit).

## 8. Working/scratch memory — explicitly OUT OF SCOPE

Ephemeral in-run state (agent scratchpad) is **not** durable memory. It is
covered by the Run lifecycle (execution context + checkpoints for pause/resume).
Adding it to the durable contract would blur retention/privacy rules. The write
into episodic/semantic/procedural memory *is* the boundary between scratch and
durable. No schema, no op; use RunControl checkpoints if persistence across
pause/resume is needed.

## 9. Migration & compatibility

- **Non-breaking:** `MemoryRecord` and its 4 ops are unchanged; episodic keeps
  working. New surfaces are additive resources.
- **Sharing:** `scope` is introduced additively; `sharingMode`/`sharedWith[]`
  are **deprecated** (retained, superseded by `scope`) pending §6 ratification.
- **Conformance:** episodic + `agent` scope = the floor. Semantic/procedural/
  provenance and `campaign`/`platform` scope land as profile extensions so
  implementations aren't forced to build everything at once.
- **Landscape (candidate conforming backends, not dependencies):** Mem0
  (semantic+episodic fusion), Letta/MemGPT (working↔durable paging), Zep/Graphiti
  (temporal KG for semantic), Cognee (graph ETL). Selected via capability
  routing behind the contract — never a hard spec dependency.

## 10. Summary

| # | Surface | Status today | New primitive | Why existing surface can't do it |
|---|---|---|---|---|
| Episodic | have | `MemoryRecord` (unchanged) | — | ✅ it's the one that works |
| Semantic | label only | `SemanticFact` | no confidence/evidence/validity/supersession → beliefs can't be revised |
| Procedural | **missing** | `Procedure` + governed `replay` | a text blob isn't executable/replayable |
| Shared | **decision** | `memory-scope` (agent/campaign/platform) | overlapping, unbounded, unenforced sharing |
| Provenance | missing | hash-chained signed `ProvenanceRecord` | records are mutable/deletable, no chain/signature |
| Working | out of scope | none (use checkpoints) | ephemeral; doesn't belong in durable contract |

**Open item for reviewers:** ratify §6. On ratification this RFC is submitted as
a PR to the ARIA spec repo (new schemas + openapi ops + README Memory tag).


# RFC 014: Contribute starter fixtures for `evaluatePolicy`, `runEval`, `getEvalResult`

**Gap IDs:** `provisional-gap-005` (provisional — replace before opening upstream)

## Problem

[`contracts/fixtures/v3/`](../fixtures/v3/) ships fixtures for most core-v3
operations (`runs-submit.request.json`, `events-append.request.json`,
`identity-session.response.json`, etc.) but is missing fixtures for:

- `evaluatePolicy` (request and response)
- `runEval` (request and response)
- `getEvalResult` (response)

[`v3-release-governance.md`](../v3-release-governance.md) `## GA exit criteria`
item 3 — "fixture suite under `fixtures/v3/` validates via `make
validate-v3-contracts`" — implicitly assumes complete fixture coverage. The
three missing operations leave a gap.

Practical consequence: implementers have no fixture to validate request /
response shapes against during build-out, so every implementer reverse-engineers
a fixture from
[`policy-check-event.schema.json`](../schemas/events/policy-check-event.schema.json),
[`eval-result.schema.json`](../schemas/common/eval-result.schema.json), and the
OpenAPI operation specs. The result is per-implementer fixture drift on shapes
that should be canonical.

## Proposal

Add five fixtures under `contracts/fixtures/v3/`:

| Fixture | Operation | Coverage |
| --- | --- | --- |
| `policy-decide.request.json` | `evaluatePolicy` | Allow, deny, and conditional decisions (three sibling fixtures) |
| `policy-decide.response.json` | `evaluatePolicy` | Response shapes plus the `policy.checked` event the decision emits (cross-referenced via `correlationId`); deny carries `failureClass: F4_POLICY` |
| `evals-run.request.json` | `runEval` | Request body declaring a `suiteId`, `inputs`, and an optional `scoringPolicy` |
| `evals-run.response.json` | `runEval` | Response returning the new `evalRunId` and a Run document in `queued` state |
| `evals-result.response.json` | `getEvalResult` | Full `EvalResult` shape (passed, failed, running examples in three sibling fixtures) |

### Validation

Each fixture validates against its target schema (`eval-result.schema.json`,
`policy-check-event.schema.json`, and the request bodies declared in
[`openapi/gmp-core-v3.yaml`](../openapi/gmp-core-v3.yaml)) and round-trips
through
[`scripts/validate_v3_contracts.py`](../../scripts/validate_v3_contracts.py)
without modification. Cross-check: the `policy.checked` event emitted by
`policy-decide.response.json` validates against `policy-check-event.schema.json`.

### Fixture-content discipline

Realistic sample values are generic — no domain-specific words. The fixtures
exercise *shape*, not *semantics*. The fixture suite is part of the GA exit
criteria; expanding it arguably warrants a release note but no version bump.

## Deferred (out of scope for this RFC)

- **Fixtures for the durable-execution stubs** (`pauseRun`, `resumeRun`,
  `listRunCheckpoints`). Those operations remain stubs in most implementations;
  fixtures should follow once the operations actually have non-501 behavior.
- **Fixtures for sandbox/supervision** (`proposeAction`, `approveAction`,
  `applyAction`, `rollbackAction`, `listSupervisionQueue`, `recordIntervention`,
  `listDivergenceAlerts`). HITL-optional; ship when an implementation actually
  wires them up.
- **Negative / error fixtures.** This RFC adds happy-path fixtures only. A
  follow-up could add `policy-decide.error.json` etc. demonstrating
  `StructuredError` shapes for each operation.

## Platform reference

[ARIAPlatform `platform-v0-implementation-profile.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/platform-v0-implementation-profile.json)
— `EvaluatePolicy`, `RunEval`, `GetEvalResult`. ARIAPlatform v0 exercises these
operations against per-implementer fixtures today; promoting starters upstream
gives the next implementer a documented baseline.

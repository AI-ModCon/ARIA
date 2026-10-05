# RFC 023: Declare `403` on `planRun` to match `submitRun`

Against `contracts/openapi/gmp-core-v3.yaml` at **`b52a06c`**
(`v0.3.5-13-gb52a06c`, `info.version: 3.0.2`) — `main` at the time of writing.
Every line number and status code below was re-derived against that commit by
parsing the document, not by reading offsets off a grep.

## Problem

`submitRun` and `planRun` take the **same required field naming the same
resource**, and declare different authorization outcomes for it.

| | `submitRun` | `planRun` |
|---|---|---|
| Path | `/v3/runs` (line 156) | `/v3/runs:plan` (line 374) |
| `capabilityId` | required, request body (line 167) | required, request body (line 385) |
| Declared responses | `202 400 401 403 409 500` | `200 400 401 500` |

Both request bodies are `required: true` and both list `capabilityId` first in
`required`. The field has the same name, same type, and the same referent — a
capability in the registry reachable at `/v3/capabilities/{capabilityId}`.

`submitRun` declares `403` (`#/components/responses/Forbidden`,
"Authenticated but not authorized for requested action"), which is the spec
acknowledging that naming a capability is not the same as being allowed to use
it. `planRun` names the same capability and does not acknowledge that.

This is an inconsistency **internal to the specification**. It is visible by
reading the document alone, and it does not depend on how any implementation
behaves.

### Why `planRun` needs it for the same reason `submitRun` does

If `403` on `submitRun` is correct, the argument for it applies to `planRun`
unchanged:

- `planRun` is in the `Negotiation` tag and returns `RunPlanSuccess` — a
  **dry run, explanation, or clarification plan** for executing the named
  capability (`summary`, line 378). That response describes the shape and cost
  of running something the caller may not be entitled to run.
- An authorization model under which a caller may obtain a costed execution
  plan for a capability it cannot submit against is a strange model to adopt
  silently. It may be a defensible one — but the spec should say so, rather
  than leave it as an omission readers must guess about.

The alternative reading is that `planRun` is deliberately ungated. If that is
the intent, it is worth stating explicitly in the operation `description`,
because the current document gives no way to distinguish *"planning is
deliberately open"* from *"the `403` was added to `submitRun` and not carried
across."*

### Consequence for generated clients

A client generated from this document gets a typed `403` branch for
`submitRun` and no `403` branch for `planRun`. A deployment that gates both —
the natural reading of `submitRun`'s `403` — produces a response the generated
`planRun` client has no case for. The two operations are adjacent steps in one
workflow (`planRun` returns a `planId`; `submitRun` accepts one at line 171),
so the same caller meets both in sequence and must handle refusal differently
for each.

## Proposal

One addition. At `planRun`'s `responses` (line 391), between `401` (line 396)
and `500`:

```yaml
        '403':
          $ref: '#/components/responses/Forbidden'
```

`Forbidden` already exists at line 1352 and already resolves to
`StructuredError`, the error body `planRun` uses for `400`, `401` and `500`.
No new component, no schema change, no new field.

This is additive and backward compatible: no previously valid request or
response becomes invalid, and no existing behavior changes meaning. An
implementation that does not gate `planRun` is unaffected — a declared response
is a permitted outcome, not a required one.

### Secondary question, not a demand

`submitRun` also declares `409` (`Conflict`) and `planRun` does not. Unlike the
`403`, there is a plausible reason for the asymmetry: `submitRun` takes a
required `idempotencyKey` (line 167) and `planRun` does not, so at least one of
`submitRun`'s conflict cases has no `planRun` analogue. Whether the
*capability-state* conflict — entitled caller, capability not active — also
warrants `409` on `planRun` is a question for the maintainers, and this RFC
does not propose it. Raised only so the answer is recorded rather than
rediscovered.

## What this RFC deliberately does **not** propose

An earlier draft of this document was wider. The following were removed after
checking them against the spec's own conventions rather than against our
implementation, and they are listed here so the same ground is not re-covered.

**A `capabilityId` field on `summarizeMemoryRecords`.** The operation (line
516) takes `required: [agentId]` and nothing else, and declares `200/401/500`.
An implementation that summarizes by invoking a model gateway must choose
*which* gateway, and the spec gives it no field — so it is tempting to ask for
one.

Withdrawn: the spec already answers this. `info.description` (lines 9–10) states
that **non-core extensions use `x-gmp-*` fields or routes under
`/v3/experimental/`**. Gateway selection is deployment topology, not control-
plane semantics — a single-gateway deployment needs no such field, and the
right place for it is `x-gmp-*`, exactly where the spec puts it. Asking core to
absorb it would be asking the spine to model our deployment shape.

**A `404` on `submitRun` and `planRun` for unknown capability ids.** Withdrawn
because it argues against a convention the spec applies consistently. All ten
operations that declare `404` identify the resource in the **path**:

```
getCapability           /v3/capabilities/{capabilityId}
getRun                  /v3/runs/{runId}
cancelRun               /v3/runs/{runId}/cancel
retryRun                /v3/runs/{runId}/retry
pauseRun                /v3/runs/{runId}/pause
resumeRun               /v3/runs/{runId}/resume
listRunCheckpoints      /v3/runs/{runId}/checkpoints
getCapabilityTokenAudit /v3/identity/capability-tokens/{tokenId}/audit
getTaskUsage            /v3/usage/tasks/{taskId}
getEvalResult           /v3/evals/{evalId}
```

**Zero** operations declare `404` for an identifier supplied in a request body.
`submitRun` and `planRun` supply `capabilityId` in the body, and the spec's
answer for an unsatisfiable body is `400`. An implementation returning `404`
there is making a local choice; the spec is not inconsistent.

**A normative `404` → `403` → `409` resolution order.** This mattered only
while `404` was in scope. With `404` withdrawn it reduces to the ordinary
question of whether an unentitled caller can distinguish a real capability id
from an invented one — a real question, but a cross-cutting one about the whole
registry, not something to settle inside a change to one operation's response
list.

## How to verify every claim above

From the repository root, against `b52a06c`:

```bash
python - <<'PY'
import yaml
d = yaml.safe_load(open('contracts/openapi/gmp-core-v3.yaml'))
for path, ops in d['paths'].items():
    for method, op in ops.items():
        if method not in ('get', 'post', 'put', 'patch', 'delete'):
            continue
        body = (op.get('requestBody') or {}).get('content', {})
        schema = body.get('application/json', {}).get('schema', {})
        if 'capabilityId' in (schema.get('properties') or {}):
            print(f"{op['operationId']:12} "
                  f"required={'capabilityId' in (schema.get('required') or [])}  "
                  f"{sorted(op['responses'])}")
PY
```

Output — the two operations whose request body declares `capabilityId`:

```
submitRun    required=True  ['202', '400', '401', '403', '409', '500']
planRun      required=True  ['200', '400', '401', '500']
```

That `Forbidden` already exists and needs no definition:

```bash
grep -n -A1 '^    Forbidden:' contracts/openapi/gmp-core-v3.yaml
```

```
1352:    Forbidden:
1353-      description: Authenticated but not authorized for requested action.
```

That `404` is a path-parameter convention — every operation declaring `404`,
with whether its path is parameterized:

```bash
python - <<'PY'
import yaml
d = yaml.safe_load(open('contracts/openapi/gmp-core-v3.yaml'))
for path, ops in d['paths'].items():
    for method, op in ops.items():
        if method in ('get', 'post', 'put', 'patch', 'delete') \
                and '404' in op['responses']:
            print(f"{op['operationId']:24} {path:46} "
                  f"path_param={'{' in path}")
PY
```

Every line reports `path_param=True`.

Scale, for context: across all **38** operations, only **two** declare `403` —
`evaluatePolicy` and `submitRun`.

## Origin

Surfaced while reviewing capability authorization in ARIAPlatform (private),
which gates `planRun` and `submitRun` on the same entitlement check and could
declare that outcome for only one of them.

The implementation is the *reason the question was asked*, not the argument
for the change: the inconsistency above is demonstrable from
`gmp-core-v3.yaml` alone, and nothing in this proposal depends on how
ARIAPlatform behaves. Where our behavior is a local choice rather than a spec
defect — the `x-gmp-*` gateway field and the body-id `404` — it stays recorded
on our side in `reference/platform-v0-implementation-profile.json`, and is
withdrawn from this proposal.

No platform links are given deliberately: that repository is private, and the
records in question sit on an unmerged branch, so a citation would be one a
reviewer can neither follow nor check. Reviewers should not need them — every
claim here is verifiable against this repository alone, with the commands
above.

---

*Drafted with AI assistance (per `CONTRIBUTING.md` §Guidelines for AI/LLM-
Assisted Contributions). All spec claims were re-derived by parsing
`gmp-core-v3.yaml` at `b52a06c` and are reproducible with the commands above.*

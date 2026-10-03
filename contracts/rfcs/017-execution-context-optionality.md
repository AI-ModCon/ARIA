# RFC 017: Make ExecutionContext seedList and dataVersion optional

## Problem

[`execution-context.schema.json`](../schemas/common/execution-context.schema.json) requires
`configHash`, `environmentHash`, `seedList` (`minItems: 1`), and `dataVersion`
(`minLength: 1`), and [`run.schema.json`](../schemas/common/run.schema.json) requires
`executionContext` on every Run. The required quartet is simulation-flavored: for an
instrument-control actor or a data-movement attempt there is no meaningful seed or dataset
version, so sites will fill garbage (`[0]`, `"n/a"`) to validate — degrading exactly the
provenance value the fields exist to provide.

## Proposal

- Drop `seedList` and `dataVersion` from the schema `required` array (loosening change;
  all existing payloads remain valid). `configHash` and `environmentHash` stay required —
  every run type has a configuration and an environment.
- Add an optional **`runClass`** discriminator to `execution-context.schema.json`:
  `enum [reproducible, analysis, operational]`. This is a property of the submitted run, not of
  the capability — `reproducibilityTiers` in `core-v3.json` (declared / smoke-tested /
  independently replicated) is a capability **maturity** claim and is deliberately not
  used here, since a smoke-tested data-movement capability must not be forced to carry a
  seed.
- Re-require conditionally, in the schema itself, so a validator enforces it without
  profile interpretation:

  ```json
  "allOf": [
    { "if":   { "properties": { "runClass": { "const": "reproducible" } },
                "required": ["runClass"] },
      "then": { "required": ["seedList", "dataVersion"] } },
    { "if":   { "properties": { "runClass": { "const": "analysis" } },
                "required": ["runClass"] },
      "then": { "required": ["dataVersion"] } }
  ]
  ```

  A `runClass: reproducible` fixture that omits `seedList` fails validation; an
  `analysis` fixture that omits `dataVersion` fails; an `operational` (or class-less)
  fixture that omits both passes. The base `required` array is not re-widened.

  The middle class is motivated by measurement. In a crosswalk of the 447 agent
  paper-replications in the public `replication-project` corpus (2026-10-03),
  tool/database version drift was the largest cause of explained divergences — an
  AMRFinderPlus 3.8.4→4.2.7 upgrade reversed a published AMR association
  (BVBRC-109), and antiSMASH v5→v6 shifted BGC counts (BVBRC-86, BVBRC-72) — and the
  affected runs are deterministic screens that carry no meaningful seed. Under a
  binary split those runs must either placeholder a seed (recreating the problem
  this RFC exists to stop) or drop `dataVersion`, the one field whose absence
  demonstrably costs reproducibility. `analysis` = deterministic computation over
  versioned external data; `reproducible` = stochastic computation where seeds and
  data versions both bind.
- Profile hook: profiles that host reproducibility-bearing science (e.g. the RFC 016
  `evals` module, or a deployment profile for simulation campaigns) add a compliance
  check **`execution_context_run_class_enforced`**, evaluated against fixtures of all three
  classes as above. `minimal-core-v3` does not require `runClass` to be present.
- Normative omission rule, carried in the schema `description` of both fields (removing
  them from `required` does not by itself reject `[0]` or `"n/a"`): *"When semantically
  inapplicable this field MUST be omitted, never filled with a placeholder; placeholder
  values are a conformance failure of the submitting implementation."*
- No change to the companion
  [`run-invocation.schema.json`](../companion/schemas/run-invocation.schema.json)
  `contextHash` linkage.

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §5.2.

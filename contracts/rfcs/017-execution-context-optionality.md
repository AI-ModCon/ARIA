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
- Re-require them profile-conditionally: reproducibility-bearing capability classes
  (simulation, training, evals — tier2/tier3 of `reproducibilityTiers`) mandate
  `seedList`/`dataVersion` via profile constraint, aligned with RFC 016 module tiering.
- Normative guidance: when semantically inapplicable the fields MUST be omitted, never
  filled with placeholders.
- No change to the companion
  [`run-invocation.schema.json`](../companion/schemas/run-invocation.schema.json)
  `contextHash` linkage.

## Reference

Surfaced by the ARIA v3 ↔ Academy integration mapping (2026-10-01), §5.2.

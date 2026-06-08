# GMP Companion Schemas

Optional JSON Schemas for **enterprise interoperability** that sit **outside** the mandatory `core-v3` profile defined in [profiles/core-v3.json](../profiles/core-v3.json). Use them when exchanging portable **campaign graphs**, **data-movement intents**, **evaluation publication metadata**, or **literal run invocation records** across sites—without widening the spine OpenAPI into a universal platform specification.

Deployments that commit to validating these artefacts may adopt **[profiles/core-v3-companion.json](../profiles/core-v3-companion.json)** in addition to the spine profile.

| Schema | File | Purpose |
| ------ | ---- | ------- |
| CampaignPlan | [schemas/campaign-plan.schema.json](schemas/campaign-plan.schema.json) | Typed DAG (nodes + edges + optional gate references); link from Run via `planRef` / `planDigest`. |
| DataMovementIntent | [schemas/data-movement-intent.schema.json](schemas/data-movement-intent.schema.json) | Declarative move/stage request; actual Globus/ObjectStore execution lives in mover **capabilities**. |
| EvalPublication | [schemas/eval-publication.schema.json](schemas/eval-publication.schema.json) | Publication / leaderboard metadata keyed to spine `suiteId` / `evalId` results. |
| RunInvocation | [schemas/run-invocation.schema.json](schemas/run-invocation.schema.json) | Literal invocation `inputs` / `parameters` and `outputs` (including MAG `tool_calls`) behind a spine `ExecutionContext`; link from Run via `contextHash`. See [run-invocation-interop.md](run-invocation-interop.md). |

**Versioning:** additive optional fields compatible with repo-wide JSON Schema conventions; companion `$id` URIs live under `https://gmp.dev/contracts/companion/schemas/`.

**Validation:** fixtures under [fixtures/companion/](../fixtures/companion/) are checked when running `make validate-v3-contracts`.

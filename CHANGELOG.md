# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to semantic-style version labels used by the ARIA spec tags.

## [Unreleased]

### Added

- Added Apache 2.0 `LICENSE`, `NOTICE`, `CONTRIBUTING.md`, and `CODE_OF_CONDUCT.md` adapted from the ModCon BaseTemplate.
- Implemented RFC 018: optional `runId` and `correlationId` on `AgentMessage` and `Handoff`, plus optional `capabilityTokenRef` and `budgetRef` on `Handoff`, so coordination records can be correlated with a Run's journal and can reference the authority and allocation the handed-off work operates under (#29).
- Added `agent-message-run-correlated.request.json` and `handoff-attenuated.request.json` fixtures with validator coverage for the RFC 018 fields.
- Implemented RFC 022: the `ExecutionAttempt` companion schema, linking one Run attempt to an external task identity (scheduler job via IRI, Globus Compute task, Globus Transfer task) with the one-non-terminal-attempt invariant, `retryRun` append semantics, and reconciliation-after-restart rules carried in the schema `description` (#33).
- Implemented RFC 012: optional `inputTokens`, `outputTokens`, `modelId`, `provider`, `modelTier`, `spendUsd`, and `uncertainty` accounting fields on the `tool.call` event payload, plus an optional `attemptId` that gives RFC 022 its `tool.call` event binding (#18).
- Implemented RFC 010: `run.cancelled` on the `RunLifecycleEvent.eventType` enum, so an initiator-driven cancellation is recorded as a first-class lifecycle event instead of a `run.failed` with a `cancelled` status (#16).
- Added `execution-attempt.example.json`, `execution-attempt-retry.example.json`, and `execution-attempt-lost.example.json` companion fixtures, plus `tool-call-event-accounting.json`, `run-lifecycle-cancelled.json`, and `events-journal-attempt.request.json` under `fixtures/v3/`, all with validator coverage. `run-lifecycle-cancelled.json` is the first direct fixture for `run-lifecycle-event.schema.json`.
- Implemented RFC 017: optional `runClass` (`reproducible`, `analysis`, `operational`) on `ExecutionContext`, which re-requires `seedList` and `dataVersion` for reproducible runs and `dataVersion` for analysis runs through in-schema `if`/`then`. Both field descriptions now state that an inapplicable field MUST be omitted rather than filled with a placeholder such as `[0]` or `"n/a"` (#28).
- Added the `execution_context_run_class_enforced` compliance check to `core-v3` and `core-v3-companion`.
- Added `execution-context-operational.request.json`, `execution-context-analysis.request.json`, and `execution-context-reproducible.request.json` fixtures, plus validator negative checks that reject a reproducible context missing `seedList` or `dataVersion` and an analysis context missing `dataVersion`.

### Changed

- Removed `seedList` and `dataVersion` from the `ExecutionContext` `required` array (RFC 017, #28). Every existing payload stays valid, but consumers can no longer assume either field is present; `configHash` and `environmentHash` remain required. They are still required when `runClass` is `reproducible` (both) or `analysis` (`dataVersion`).
- Taught the contract validator to evaluate `if`/`then`/`else` and `const`, which it previously ignored, so the RFC 017 conditional would have passed any payload. `allOf` no longer short-circuits sibling keywords, so a schema that combines `allOf` with top-level `properties` and `required` is now checked in full.
- Recorded in `v3-release-governance.md` that removing a field from a schema `required` array is a contract minor.
- Bumped `core-v3` and `core-v3-companion` profiles and the `gmp-core-v3.yaml` description revision to 3.1.0 for RFC 017.

- Taught the contract validator to resolve JSON-pointer `$ref` fragments (for example `model-routing-policy.schema.json#/properties/defaultTier`), which previously reported as unresolved.
- Aligned RFC process documentation with the implementation-ready workflow: the RFC PR now stays open during implementation and merges after the implementation PR lands (#25).
- Added GitHub issue and pull request templates under `.github/`.
- Bumped `core-v3` and `core-v3-companion` profiles and the `gmp-core-v3.yaml` description revision to 3.0.2 for the additive RFC 018 fields, then to 3.0.3 for the additive RFC 022, RFC 012, and RFC 010 changes.

## [v0.3.5] - 2026-06-11

### Added

- Added this changelog.
- Added RFC 005 as the normative record for events append/list DTO alignment over the canonical `GmpEvent` envelope.
- Added append-projection and list-response fixtures (including cursor pagination without `total`) with validator coverage.

### Changed

- Updated `appendEvent` in `gmp-core-v3.yaml` to accept the RFC 005 append projection, return `201 Created` with `Location` and `{"eventId"}`, and document `422` validation against the canonical `oneOf`.
- Updated `listEvents` to return `EventListItem` projections with `(occurredAt, eventId)` ordering, cursor pagination, expanded v0 filters, and deprecated `offset`.

## [v0.3.4] - 2026-06-09

### Added

- Added RFC 001 as the record for run invocation I/O and MAG `tool_calls` alignment.
- Added the `RunInvocation` companion schema for literal invocation `inputs`, `parameters`, and normalized `outputs.tool_calls` without widening the mandatory core-v3 spine.
- Added `run-invocation-interop.md` documenting OpenAI/Anthropic MAG normalization and the boundary between model-turn records and executed-tool telemetry.
- Added a companion fixture and validator coverage for `RunInvocation`.
- Added the RFC process directory under `contracts/rfcs/` with an index and suggested merge order for the platform v0 alignment RFC series.
- Added background source documents under `background/` for agent-oriented architecture and requirement walkthrough context.

### Changed

- Updated the core-v3 companion profile to include `RunInvocation`.
- Tightened `RunInvocation.contextHash` and `outputs.tool_calls[]` validation to match the platform alignment contract.

## [v0.3.3] - 2026-05-12

### Added

- Added the root README with ARIA branding and a note about the former GM API Specification repository.

## [v0.3.2] - 2026-05-08

### Changed

- Normalized the canonical specification layout under `contracts/`.
- Moved extracted OpenAPI, JSON Schema, profile, fixture, and governance assets into the `contracts/` root.
- Updated validation tooling and path references for the split specification repository.

## [v_0.3.1] - 2026-05-04

### Added

- Added the `core-v3-companion` profile.
- Added companion schemas and fixtures for `CampaignPlan`, `DataMovementIntent`, and `EvalPublication`.
- Added classification shift events to the v3 event taxonomy.
- Added uncertainty modeling to common schemas and profile coverage.

### Changed

- Expanded the core-v3 gap disposition register for spine, companion, capability-profile, experimental, and out-of-scope items.
- Refreshed documentation and validator coverage for the expanded companion bundle.

## [v_0.3] - 2026-04-29

### Added

- Added GMP core-v3 OpenAPI, profile, schemas, fixtures, governance notes, and validation tooling.
- Added historical archives for v1 and v2 contracts under `contracts/archive/`.

### Changed

- Restructured the repository around the GMP core-v3 contract baseline.
- Refreshed Makefile targets and README documentation for the v3 layout.

## [v_0.2] - 2026-04-28

### Added

- Added GMP core-v2 OpenAPI and profile definitions.
- Added extended JSON Schemas and example fixtures for the v2 contract line.
- Added migration documentation, Makefile targets, and validation scripts.

## [v_0.1] - 2026-04-28

### Added

- Added the initial contracts package baseline.
- Added repository-level documentation for the contracts layout and tracked files.

[Unreleased]: https://github.com/AI-ModCon/ARIA/compare/v0.3.5...HEAD
[v0.3.5]: https://github.com/AI-ModCon/ARIA/compare/v0.3.4...v0.3.5
[v0.3.4]: https://github.com/AI-ModCon/ARIA/releases/tag/v0.3.4
[v0.3.3]: https://github.com/AI-ModCon/ARIA/releases/tag/v0.3.3
[v0.3.2]: https://github.com/AI-ModCon/ARIA/releases/tag/v0.3.2
[v_0.3.1]: https://github.com/AI-ModCon/ARIA/releases/tag/v_0.3.1
[v_0.3]: https://github.com/AI-ModCon/ARIA/releases/tag/v_0.3
[v_0.2]: https://github.com/AI-ModCon/ARIA/releases/tag/v_0.2
[v_0.1]: https://github.com/AI-ModCon/ARIA/releases/tag/v_0.1

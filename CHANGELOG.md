# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to semantic-style version labels used by the ARIA spec tags.

## [Unreleased]

### Added

- Added this changelog.

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

[Unreleased]: https://github.com/brettin/ARIA/compare/v0.3.4...HEAD
[v0.3.4]: https://github.com/brettin/ARIA/releases/tag/v0.3.4
[v0.3.3]: https://github.com/brettin/ARIA/releases/tag/v0.3.3
[v0.3.2]: https://github.com/brettin/ARIA/releases/tag/v0.3.2
[v_0.3.1]: https://github.com/brettin/ARIA/releases/tag/v_0.3.1
[v_0.3]: https://github.com/brettin/ARIA/releases/tag/v_0.3
[v_0.2]: https://github.com/brettin/ARIA/releases/tag/v_0.2
[v_0.1]: https://github.com/brettin/ARIA/releases/tag/v_0.1

# RFC 006: Capability registry vs spec Capability

## Problem

Spec `Capability` requires `profile`, `executionContext`, `artifact`, smoke-test status enum. Platform registry exposes `capabilityType`, `routing`, `owner`, MAG metadata.

## Proposal

Companion `platform-capability.schema.json` for registration API; keep spec Capability for scientific artifact binding.

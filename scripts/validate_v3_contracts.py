#!/usr/bin/env python3
"""Validate GMP v3 contract fixtures and profile references.

Dependency-free validator (stdlib only). It checks:
1) v3 envelope files exist
2) core-v3 plus core-v3-companion profile required schema paths resolve
3) schema and fixture files are valid JSON (including companion/schemas)
4) fixture payloads satisfy recursive required/type/enum/allOf/oneOf/$ref rules
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
SCHEMAS_COMMON = CONTRACTS / "schemas" / "common"
SCHEMAS_EVENTS = CONTRACTS / "schemas" / "events"
SCHEMAS_COMPANION = CONTRACTS / "companion" / "schemas"
FIXTURES = CONTRACTS / "fixtures" / "v3"
FIXTURES_COMPANION = CONTRACTS / "fixtures" / "companion"
PROFILE_V3 = CONTRACTS / "profiles" / "core-v3.json"
PROFILE_V3_COMPANION = CONTRACTS / "profiles" / "core-v3-companion.json"
OPENAPI_V3 = CONTRACTS / "openapi" / "gmp-core-v3.yaml"


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _collect_schema_store() -> tuple[dict[str, dict], dict[Path, dict]]:
    by_id: dict[str, dict] = {}
    by_path: dict[Path, dict] = {}
    paths: list[Path] = list(SCHEMAS_COMMON.glob("*.json")) + list(SCHEMAS_EVENTS.glob("*.json"))
    if SCHEMAS_COMPANION.exists():
        paths.extend(SCHEMAS_COMPANION.glob("*.json"))
    for schema_path in paths:
        schema = _read_json(schema_path)
        by_path[schema_path.resolve()] = schema
        schema_id = schema.get("$id")
        if isinstance(schema_id, str):
            by_id[schema_id] = schema
    return by_id, by_path


def _matches_type(value: object, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    return True


def _resolve_ref(ref: str, current_schema_path: Path, schemas_by_id: dict[str, dict], schemas_by_path: dict[Path, dict]) -> tuple[dict | None, Path | None]:
    if ref.startswith("#"):
        return None, None
    if ref.startswith("http://") or ref.startswith("https://"):
        return schemas_by_id.get(ref), None
    target_path = (current_schema_path.parent / ref).resolve()
    return schemas_by_path.get(target_path), target_path


def _validate_instance(
    instance: object,
    schema: dict,
    schema_path: Path,
    context: str,
    schemas_by_id: dict[str, dict],
    schemas_by_path: dict[Path, dict],
) -> list[str]:
    errors: list[str] = []

    if "$ref" in schema:
        ref = schema["$ref"]
        if not isinstance(ref, str):
            return [f"{context}: invalid $ref type"]
        resolved, resolved_path = _resolve_ref(ref, schema_path, schemas_by_id, schemas_by_path)
        if resolved is None:
            return [f"{context}: unresolved $ref '{ref}'"]
        next_path = resolved_path if resolved_path is not None else schema_path
        return _validate_instance(instance, resolved, next_path, context, schemas_by_id, schemas_by_path)

    if "oneOf" in schema:
        one_of = schema.get("oneOf")
        if isinstance(one_of, list) and one_of:
            for idx, subschema in enumerate(one_of):
                if isinstance(subschema, dict):
                    branch_errs = _validate_instance(
                        instance,
                        subschema,
                        schema_path,
                        f"{context}.oneOf[{idx}]",
                        schemas_by_id,
                        schemas_by_path,
                    )
                    if not branch_errs:
                        return []
            return [f"{context}: no oneOf branch validated"]
        return errors

    if "allOf" in schema:
        all_of = schema.get("allOf", [])
        if isinstance(all_of, list):
            for idx, subschema in enumerate(all_of):
                if isinstance(subschema, dict):
                    errors.extend(
                        _validate_instance(
                            instance,
                            subschema,
                            schema_path,
                            f"{context}.allOf[{idx}]",
                            schemas_by_id,
                            schemas_by_path,
                        )
                    )
        return errors

    expected_type = schema.get("type")
    if isinstance(expected_type, list):
        if not any(_matches_type(instance, t) for t in expected_type if isinstance(t, str)):
            errors.append(f"{context}: expected type one of {expected_type}, got {type(instance).__name__}")
            return errors
    elif isinstance(expected_type, str):
        if not _matches_type(instance, expected_type):
            errors.append(f"{context}: expected type '{expected_type}', got {type(instance).__name__}")
            return errors

    if "enum" in schema and isinstance(schema["enum"], list):
        if instance not in schema["enum"]:
            errors.append(f"{context}: value '{instance}' not in enum {schema['enum']}")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for field in required:
                if isinstance(field, str) and field not in instance:
                    errors.append(f"{context}: missing required field '{field}'")

        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, value in instance.items():
                if key in properties and isinstance(properties[key], dict):
                    errors.extend(
                        _validate_instance(
                            value,
                            properties[key],
                            schema_path,
                            f"{context}.{key}",
                            schemas_by_id,
                            schemas_by_path,
                        )
                    )
                elif schema.get("additionalProperties") is False:
                    errors.append(f"{context}: unexpected field '{key}'")
            additional = schema.get("additionalProperties")
            if isinstance(additional, dict):
                for key, value in instance.items():
                    if key not in properties:
                        errors.extend(
                            _validate_instance(
                                value,
                                additional,
                                schema_path,
                                f"{context}.{key}",
                                schemas_by_id,
                                schemas_by_path,
                            )
                        )

    if isinstance(instance, list):
        items_schema = schema.get("items")
        if isinstance(items_schema, dict):
            for idx, item in enumerate(instance):
                errors.extend(
                    _validate_instance(
                        item,
                        items_schema,
                        schema_path,
                        f"{context}[{idx}]",
                        schemas_by_id,
                        schemas_by_path,
                    )
                )

    return errors


def main() -> int:
    errors: list[str] = []

    if not OPENAPI_V3.exists():
        errors.append(f"Missing required API spec: {OPENAPI_V3}")
    if not PROFILE_V3.exists():
        errors.append(f"Missing required profile: {PROFILE_V3}")
    if not PROFILE_V3_COMPANION.exists():
        errors.append(f"Missing companion profile: {PROFILE_V3_COMPANION}")

    try:
        profile = _read_json(PROFILE_V3)
    except Exception as exc:
        errors.append(f"Failed to parse {PROFILE_V3}: {exc}")
        profile = {}

    companion_profile: dict = {}
    if PROFILE_V3_COMPANION.exists():
        try:
            companion_profile = _read_json(PROFILE_V3_COMPANION)
        except Exception as exc:
            errors.append(f"Failed to parse {PROFILE_V3_COMPANION}: {exc}")

    for rel in profile.get("requiredSchemas", []):
        full_path = (PROFILE_V3.parent / rel).resolve()
        if not full_path.exists():
            errors.append(f"Missing required schema from profile: {rel}")
        else:
            try:
                _read_json(full_path)
            except Exception as exc:
                errors.append(f"Failed to parse schema {rel}: {exc}")

    for rel in companion_profile.get("requiredSchemas", []) if companion_profile else []:
        full_path = (PROFILE_V3_COMPANION.parent / rel).resolve()
        if not full_path.exists():
            errors.append(f"Missing required schema from companion profile: {rel}")
        else:
            try:
                _read_json(full_path)
            except Exception as exc:
                errors.append(f"Failed to parse companion schema {rel}: {exc}")

    schemas_by_id, schemas_by_path = _collect_schema_store()

    direct_mappings = {
        "capability-token-mint.request.json": SCHEMAS_COMMON / "capability-token.schema.json",
        "memory-record.request.json": SCHEMAS_COMMON / "memory-record.schema.json",
        "usage-meter.response.json": SCHEMAS_COMMON / "usage-meter.schema.json",
        "budget-policy.request.json": SCHEMAS_COMMON / "budget-policy.schema.json",
        "workflow-state.response.json": SCHEMAS_COMMON / "workflow-state.schema.json",
        "reasoning-node-event.json": SCHEMAS_EVENTS / "reasoning-node-event.schema.json",
        "tool-call-event.json": SCHEMAS_EVENTS / "tool-call-event.schema.json",
        "agent-message.request.json": SCHEMAS_COMMON / "agent-message.schema.json",
        "handoff.request.json": SCHEMAS_COMMON / "handoff.schema.json",
        "consensus-decision.response.json": SCHEMAS_COMMON / "consensus-decision.schema.json",
        "side-effect-manifest.request.json": SCHEMAS_COMMON / "side-effect-manifest.schema.json",
        "approval-gate.request.json": SCHEMAS_COMMON / "approval-gate.schema.json",
        "intervention-record.request.json": SCHEMAS_COMMON / "intervention-record.schema.json",
        "identity-session.response.json": SCHEMAS_COMMON / "identity-session.schema.json",
        "events-journal-append.request.json": SCHEMAS_EVENTS / "event-envelope.schema.json",
        "classification-shift-event.json": SCHEMAS_EVENTS / "event-envelope.schema.json",
    }

    for fixture_name, schema_path in direct_mappings.items():
        fixture_path = FIXTURES / fixture_name
        if not fixture_path.exists():
            errors.append(f"Missing fixture: {fixture_path}")
            continue
        if not schema_path.exists():
            errors.append(f"Missing schema: {schema_path}")
            continue
        try:
            fixture = _read_json(fixture_path)
            schema = _read_json(schema_path)
            errors.extend(
                _validate_instance(
                    fixture,
                    schema,
                    schema_path.resolve(),
                    str(fixture_path),
                    schemas_by_id,
                    schemas_by_path,
                )
            )
        except Exception as exc:
            errors.append(f"Validation error for {fixture_path}: {exc}")

    wrapper_schemas = {
        "runs-plan.response.json": {
            "type": "object",
            "required": ["negotiation", "costLatencyHint"],
            "properties": {
                "negotiation": {"$ref": "https://gmp.dev/contracts/schemas/common/negotiation-hint.schema.json"},
                "costLatencyHint": {"$ref": "https://gmp.dev/contracts/schemas/common/cost-latency-hint.schema.json"},
            },
            "additionalProperties": False,
        },
        "checkpoint-list.response.json": {
            "type": "object",
            "required": ["items"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"$ref": "https://gmp.dev/contracts/schemas/common/checkpoint.schema.json"},
                }
            },
            "additionalProperties": False,
        },
        "supervision-queue.response.json": {
            "type": "object",
            "required": ["items"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"$ref": "https://gmp.dev/contracts/schemas/common/supervision-queue-item.schema.json"},
                }
            },
            "additionalProperties": False,
        },
        "divergence-alert.response.json": {
            "type": "object",
            "required": ["items"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"$ref": "https://gmp.dev/contracts/schemas/common/divergence-alert.schema.json"},
                }
            },
            "additionalProperties": False,
        },
        # RFC 005 append projection: clients MUST omit eventId/occurredAt/source.
        "events-append.request.json": {
            "type": "object",
            "required": ["eventType", "payload"],
            "properties": {
                "eventType": {"type": "string"},
                "payload": {"type": "object"},
                "runId": {"type": "string"},
                "agentId": {"type": "string"},
                "correlationId": {"type": "string"},
                "metadata": {"type": "object"},
            },
            "additionalProperties": False,
        },
        # RFC 005 list projection: EventListItem items plus cursor pagination envelope.
        "events-list.response.json": {
            "type": "object",
            "required": ["items"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["eventId", "eventType", "occurredAt", "source", "payload"],
                        "properties": {
                            "eventId": {"type": "string"},
                            "eventType": {"type": "string"},
                            "occurredAt": {"type": "string", "format": "date-time"},
                            "source": {"type": "string"},
                            "payload": {"type": "object"},
                            "correlationId": {"type": "string"},
                            "runId": {"type": "string"},
                            "agentId": {"type": "string"},
                            "metadata": {"type": "object"},
                        },
                        "additionalProperties": False,
                    },
                },
                "nextCursor": {"type": ["string", "null"]},
                "total": {"type": "integer"},
            },
            "additionalProperties": False,
        },
        "events-list-no-total.response.json": {
            "type": "object",
            "required": ["items"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["eventId", "eventType", "occurredAt", "source", "payload"],
                        "properties": {
                            "eventId": {"type": "string"},
                            "eventType": {"type": "string"},
                            "occurredAt": {"type": "string", "format": "date-time"},
                            "source": {"type": "string"},
                            "payload": {"type": "object"},
                            "correlationId": {"type": "string"},
                            "runId": {"type": "string"},
                            "agentId": {"type": "string"},
                            "metadata": {"type": "object"},
                        },
                        "additionalProperties": False,
                    },
                },
                "nextCursor": {"type": ["string", "null"]},
                "total": {"type": "integer"},
            },
            "additionalProperties": False,
        },
        "runs-submit.request.json": {
            "type": "object",
            "required": ["capabilityId", "executionContext", "idempotencyKey"],
            "properties": {
                "capabilityId": {"type": "string"},
                "planId": {"type": "string"},
                "planRef": {"type": "string", "format": "uri"},
                "planDigest": {"type": "string", "pattern": "^[a-fA-F0-9]{64}$"},
                "executionContext": {"$ref": "https://gmp.dev/contracts/schemas/common/execution-context.schema.json"},
                "idempotencyKey": {"type": "string"},
                "targetStrategy": {
                    "type": "object",
                    "required": ["mode", "targets"],
                    "properties": {
                        "mode": {"type": "string"},
                        "targets": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                    },
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        },
    }

    for fixture_name, wrapper_schema in wrapper_schemas.items():
        fixture_path = FIXTURES / fixture_name
        if not fixture_path.exists():
            errors.append(f"Missing fixture: {fixture_path}")
            continue
        try:
            fixture = _read_json(fixture_path)
            errors.extend(
                _validate_instance(
                    fixture,
                    wrapper_schema,
                    (SCHEMAS_COMMON / "inline-wrapper.schema.json").resolve(),
                    str(fixture_path),
                    schemas_by_id,
                    schemas_by_path,
                )
            )
        except Exception as exc:
            errors.append(f"Failed to parse fixture {fixture_path}: {exc}")

    companion_schema_dir = SCHEMAS_COMPANION
    companion_mappings: list[tuple[str, Path]] = [
        ("campaign-plan.example.json", companion_schema_dir / "campaign-plan.schema.json"),
        ("data-movement-intent.example.json", companion_schema_dir / "data-movement-intent.schema.json"),
        ("eval-publication.example.json", companion_schema_dir / "eval-publication.schema.json"),
        ("run-invocation.example.json", companion_schema_dir / "run-invocation.schema.json"),
    ]
    if not FIXTURES_COMPANION.exists():
        errors.append(f"Missing companion fixtures directory: {FIXTURES_COMPANION}")
    else:
        for fixture_name, schema_path in companion_mappings:
            fixture_path = FIXTURES_COMPANION / fixture_name
            if not fixture_path.exists():
                errors.append(f"Missing companion fixture: {fixture_path}")
                continue
            if not schema_path.exists():
                errors.append(f"Missing companion schema: {schema_path}")
                continue
            try:
                fixture = _read_json(fixture_path)
                schema = _read_json(schema_path)
                errors.extend(
                    _validate_instance(
                        fixture,
                        schema,
                        schema_path.resolve(),
                        str(fixture_path),
                        schemas_by_id,
                        schemas_by_path,
                    )
                )
            except Exception as exc:
                errors.append(f"Validation error for {fixture_path}: {exc}")

    if errors:
        print("v3 contract validation failed:\n")
        for err in errors:
            print(f"- {err}")
        return 1

    print("v3 contract validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

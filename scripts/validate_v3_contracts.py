#!/usr/bin/env python3
"""Validate GMP v3 contract fixtures and profile references.

Dependency-free validator (stdlib only). It checks:
1) v3 envelope files exist
2) core-v3 plus core-v3-companion profile required schema paths resolve
3) schema and fixture files are valid JSON (including companion/schemas)
4) fixture payloads satisfy recursive required/type/enum/pattern/allOf/oneOf/$ref rules
"""

from __future__ import annotations

import json
import re
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


class PointerError(ValueError):
    """A JSON pointer is syntactically invalid or does not name a usable subschema."""


def _unescape_token(token: str) -> str:
    """RFC 6901 section 4 unescaping. Order matters: '~1' before '~0'.

    Unescaping '~0' first would rewrite '~01' to '~1' and then to '/', losing the
    literal '~1' the author encoded.
    """
    return token.replace("~1", "/").replace("~0", "~")


def _is_array_index(token: str) -> bool:
    """RFC 6901 section 4 array index: '0', or [1-9][0-9]* with no leading zero.

    str.isdigit() alone is too permissive: it accepts leading zeros ('01') and
    non-ASCII digits.
    """
    if not token.isascii() or not token.isdigit():
        return False
    return token == "0" or not token.startswith("0")


def _resolve_pointer(document: object, pointer: str) -> dict | None:
    """Resolve an RFC 6901 JSON pointer against a document.

    Returns the referenced subschema, or None when the pointer is well formed but
    names no such member. Raises PointerError when the pointer is syntactically
    invalid or resolves to something that is not an object subschema, so a typo
    surfaces as an error instead of silently resolving.

    '' and '/' are different pointers: '' is the whole document, '/' is the
    member whose key is the empty string.
    """
    if pointer == "":
        return document if isinstance(document, dict) else None
    if not pointer.startswith("/"):
        raise PointerError(
            f"JSON pointer '{pointer}' must be empty or begin with '/' (RFC 6901 section 3)"
        )
    current: object = document
    # Split after the leading '/' only; '//x' is the two tokens ['', 'x'], not ['x'].
    for raw_token in pointer.split("/")[1:]:
        token = _unescape_token(raw_token)
        if isinstance(current, list):
            if not _is_array_index(token) or int(token) >= len(current):
                return None
            current = current[int(token)]
        elif isinstance(current, dict):
            if token not in current:
                return None
            current = current[token]
        else:
            return None
    if not isinstance(current, dict):
        raise PointerError(
            f"JSON pointer '{pointer}' resolves to {type(current).__name__}, not an object subschema"
        )
    return current


def _resolve_ref(ref: str, current_schema_path: Path, schemas_by_id: dict[str, dict], schemas_by_path: dict[Path, dict]) -> tuple[dict | None, Path | None]:
    """Resolve a $ref to a subschema. Raises PointerError on a malformed pointer."""
    base, has_fragment, pointer = ref.partition("#")
    if not base:
        # Same-document reference.
        if not has_fragment:
            raise PointerError(f"$ref '{ref}' is empty")
        if pointer == "":
            # '#' is the current document root; validating it would recurse forever.
            raise PointerError("$ref '#' (self-reference to document root) is not supported")
        document = schemas_by_path.get(current_schema_path.resolve())
        if document is None:
            return None, None
        return _resolve_pointer(document, pointer), current_schema_path
    if base.startswith("http://") or base.startswith("https://"):
        document = schemas_by_id.get(base)
        target_path = None
    else:
        target_path = (current_schema_path.parent / base).resolve()
        document = schemas_by_path.get(target_path)
    if document is None:
        return None, target_path
    if not has_fragment or pointer == "":
        # No fragment, or an empty pointer, both name the whole document.
        return document, target_path
    return _resolve_pointer(document, pointer), target_path


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
        try:
            resolved, resolved_path = _resolve_ref(ref, schema_path, schemas_by_id, schemas_by_path)
        except PointerError as exc:
            return [f"{context}: invalid $ref '{ref}': {exc}"]
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

    # JSON Schema 'pattern' applies to string instances only and is
    # unanchored (re.search semantics), per the spec; schemas that need
    # full-string matches anchor explicitly with ^...$.
    if "pattern" in schema and isinstance(instance, str):
        pattern = schema["pattern"]
        if not isinstance(pattern, str):
            errors.append(f"{context}: schema 'pattern' must be a string, got {type(pattern).__name__}")
        else:
            try:
                if re.search(pattern, instance) is None:
                    errors.append(f"{context}: value '{instance}' does not match pattern '{pattern}'")
            except re.error as exc:
                errors.append(f"{context}: schema pattern '{pattern}' is not a valid regex: {exc}")

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


def _pattern_self_test() -> list[str]:
    """Check the 'pattern' keyword binds and keeps JSON Schema semantics.

    Before this keyword was evaluated, a 64-hex field such as
    ExecutionContext.configHash accepted values like 'sha256:<hex>' (71
    characters against ^[a-fA-F0-9]{64}$) — found on the v4 draft fixtures in
    the #34 review. A green suite cannot show the keyword binds, so these
    cases run on every invocation; stdlib only, no test framework.
    """
    hex64 = "deadbeef" * 8
    hash_schema = {"type": "string", "pattern": "^[a-fA-F0-9]{64}$"}

    def validate(instance: object, schema: dict, label: str) -> list[str]:
        return _validate_instance(instance, schema, Path("pattern-self-test"), label, {}, {})

    failures: list[str] = []
    # Anchored pattern: canonical 64-hex accepted, prefixed/truncated rejected.
    if validate(hex64, hash_schema, "hex64"):
        failures.append("canonical 64-hex value was rejected")
    for label, bad in (("prefixed", f"sha256:{hex64}"), ("truncated", hex64[:-1]), ("non-hex", "z" * 64)):
        if not validate(bad, hash_schema, label):
            failures.append(f"{label} hash value was accepted; pattern is not enforced")
    # Unanchored semantics: 'pattern' uses re.search, not fullmatch.
    if validate("deadbeefcafe", {"type": "string", "pattern": "beef"}, "unanchored"):
        failures.append("unanchored pattern failed to match a substring (fullmatch semantics?)")
    # Non-string instances are out of scope for 'pattern'.
    if validate(7, {"pattern": "^[0-9]$"}, "non-string"):
        failures.append("pattern was applied to a non-string instance")
    # A malformed regex is a reported schema error, not a crash.
    try:
        if not validate(hex64, {"type": "string", "pattern": "["}, "bad-regex"):
            failures.append("malformed schema regex was not reported")
    except re.error:
        failures.append("malformed schema regex raised instead of being reported")

    return [f"Pattern self-test: {f}" for f in failures]


def _pointer_self_test() -> list[str]:
    """Check _resolve_pointer against RFC 6901 semantics.

    The resolver is exercised by only one production $ref today
    ('model-routing-policy.schema.json#/properties/defaultTier'), which would
    still pass under several incorrect implementations. These cases pin the
    general behaviour so a future fragment $ref cannot rely on a silent bug.
    Runs on every invocation; stdlib only, no test framework.
    """
    # Values are objects because _resolve_pointer only returns object subschemas.
    root = {"rootMarker": True}
    empty_key = {"emptyKeyMarker": True}
    nested_empty = {"nestedEmptyMarker": True}
    slash_key = {"slashKeyMarker": True}
    tilde_key = {"tildeKeyMarker": True}
    tilde_one_key = {"tildeOneMarker": True}
    item0 = {"itemMarker": 0}
    item1 = {"itemMarker": 1}
    doc = dict(root)
    doc.update(
        {
            "": empty_key,
            "a/b": slash_key,
            "m~n": tilde_key,
            "~1": tilde_one_key,
            "arr": [item0, item1],
            "properties": {"defaultTier": {"enum": ["cheap_fast"]}},
            "nested": {"": nested_empty},
            "scalar": 7,
        }
    )
    doc[""] = empty_key
    empty_key["deep"] = nested_empty

    # (pointer, expected) where expected is an object, None (no such member),
    # or PointerError (malformed pointer / non-object target).
    cases: list[tuple[str, object]] = [
        ("", doc),                                  # whole document
        ("/", empty_key),                           # member with the empty key, NOT the root
        ("//deep", nested_empty),                   # tokens ['', 'deep']
        ("/nested/", nested_empty),                 # trailing empty token
        ("/a~1b", slash_key),                       # ~1 unescapes to '/'
        ("/m~0n", tilde_key),                       # ~0 unescapes to '~'
        ("/~01", tilde_one_key),                    # ~01 is literal '~1', not '/'
        ("/arr/0", item0),                          # array index
        ("/arr/1", item1),
        ("/properties/defaultTier", doc["properties"]["defaultTier"]),
        ("/arr/2", None),                           # index out of range
        ("/arr/01", None),                          # leading zero is not an index
        ("/arr/-", None),                           # '-' (append) names no member
        ("/missing", None),                         # absent key
        ("/scalar/deeper", None),                   # cannot descend through a scalar
        ("properties/defaultTier", PointerError),   # missing leading '/'
        ("a", PointerError),
        ("/scalar", PointerError),                  # resolves to a non-object
    ]

    failures: list[str] = []
    for pointer, expected in cases:
        try:
            got: object = _resolve_pointer(doc, pointer)
        except PointerError:
            got = PointerError
        if expected is PointerError:
            if got is not PointerError:
                failures.append(f"pointer {pointer!r}: expected PointerError, got {got!r}")
        elif expected is None:
            if got is not None:
                failures.append(f"pointer {pointer!r}: expected None, got {got!r}")
        elif got is not expected:
            failures.append(f"pointer {pointer!r}: expected {expected!r}, got {got!r}")

    if _unescape_token("~01") != "~1":
        failures.append("unescape order wrong: '~01' must become '~1', not '/'")
    for token, want in (("0", True), ("10", True), ("01", False), ("", False), ("-", False), ("1x", False)):
        if _is_array_index(token) is not want:
            failures.append(f"array index check wrong for {token!r}: expected {want}")

    return [f"Pointer self-test: {f}" for f in failures]


def main() -> int:
    errors: list[str] = []

    errors.extend(_pointer_self_test())
    errors.extend(_pattern_self_test())

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
        "tool-call-event-accounting.json": SCHEMAS_EVENTS / "tool-call-event.schema.json",
        "run-lifecycle-cancelled.json": SCHEMAS_EVENTS / "run-lifecycle-event.schema.json",
        "agent-message.request.json": SCHEMAS_COMMON / "agent-message.schema.json",
        "agent-message-run-correlated.request.json": SCHEMAS_COMMON / "agent-message.schema.json",
        "handoff.request.json": SCHEMAS_COMMON / "handoff.schema.json",
        "handoff-attenuated.request.json": SCHEMAS_COMMON / "handoff.schema.json",
        "consensus-decision.response.json": SCHEMAS_COMMON / "consensus-decision.schema.json",
        "side-effect-manifest.request.json": SCHEMAS_COMMON / "side-effect-manifest.schema.json",
        "approval-gate.request.json": SCHEMAS_COMMON / "approval-gate.schema.json",
        "intervention-record.request.json": SCHEMAS_COMMON / "intervention-record.schema.json",
        "identity-session.response.json": SCHEMAS_COMMON / "identity-session.schema.json",
        "events-journal-append.request.json": SCHEMAS_EVENTS / "event-envelope.schema.json",
        "events-journal-attempt.request.json": SCHEMAS_EVENTS / "event-envelope.schema.json",
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
        ("execution-attempt.example.json", companion_schema_dir / "execution-attempt.schema.json"),
        ("execution-attempt-retry.example.json", companion_schema_dir / "execution-attempt.schema.json"),
        ("execution-attempt-lost.example.json", companion_schema_dir / "execution-attempt.schema.json"),
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

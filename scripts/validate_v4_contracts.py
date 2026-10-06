#!/usr/bin/env python3
"""Validate GMP v4-draft contract surface (additive alongside v3).

Dependency-free validator (stdlib only), reusing the v3 validation engine.
It checks:
1) gmp-core-v4.yaml exists and carries the same 38 operationIds as v3
2) consensus/divergence operations live under /v4/experimental/
3) v4 profiles (minimal, modules, federation) load and their schema paths resolve
4) minimal + module + experimental operations partition the v4 surface exactly
5) federation conformance levels reference defined modules only
6) v4 schemas and fixtures are valid JSON and fixtures satisfy their schemas
7) the v4 loosenings are real: a v4 fixture that drops a v3-required field
   must fail validation against the corresponding v3 schema
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_v3_contracts as v3  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
SCHEMAS_V4 = CONTRACTS / "schemas" / "v4"
FIXTURES_V4 = CONTRACTS / "fixtures" / "v4"
OPENAPI_V3 = CONTRACTS / "openapi" / "gmp-core-v3.yaml"
OPENAPI_V4 = CONTRACTS / "openapi" / "gmp-core-v4.yaml"
PROFILE_MINIMAL = CONTRACTS / "profiles" / "core-v4-minimal.json"
PROFILE_MODULES = CONTRACTS / "profiles" / "core-v4-modules.json"
PROFILE_FEDERATION = CONTRACTS / "profiles" / "federation-v4.json"


def _operation_ids(openapi_path: Path) -> set[str]:
    return set(re.findall(r"operationId: (\w+)", openapi_path.read_text(encoding="utf-8")))


def _collect_store() -> tuple[dict[str, dict], dict[Path, dict]]:
    by_id, by_path = v3._collect_schema_store()
    for schema_path in SCHEMAS_V4.glob("*.json"):
        schema = v3._read_json(schema_path)
        by_path[schema_path.resolve()] = schema
        schema_id = schema.get("$id")
        if isinstance(schema_id, str):
            by_id[schema_id] = schema
    return by_id, by_path


def main() -> int:
    errors: list[str] = []

    # 1) OpenAPI v4 present, operation set preserved
    if not OPENAPI_V4.exists():
        print(f"FAIL: missing {OPENAPI_V4}")
        return 1
    ops_v3 = _operation_ids(OPENAPI_V3)
    ops_v4 = _operation_ids(OPENAPI_V4)
    if ops_v3 != ops_v4:
        errors.append(f"v4 operationId drift vs v3: {sorted(ops_v3 ^ ops_v4)}")

    # 2) demoted operations are experimental routes
    v4_text = OPENAPI_V4.read_text(encoding="utf-8")
    for route in ("/v4/experimental/agents/{agentId}/consensus",
                  "/v4/experimental/supervision/alerts"):
        if f"  {route}:" not in v4_text:
            errors.append(f"Expected experimental route missing: {route}")
    if "/v3/" in v4_text:
        errors.append("gmp-core-v4.yaml still references /v3/ paths")

    # 3) profiles load, schema paths resolve
    minimal = v3._read_json(PROFILE_MINIMAL)
    modules_profile = v3._read_json(PROFILE_MODULES)
    federation = v3._read_json(PROFILE_FEDERATION)
    modules = modules_profile["modules"]

    def check_schema_paths(rels: list[str], label: str) -> None:
        for rel in rels:
            full = (PROFILE_MINIMAL.parent / rel).resolve()
            if not full.exists():
                errors.append(f"Missing schema from {label}: {rel}")
            else:
                try:
                    v3._read_json(full)
                except Exception as exc:
                    errors.append(f"Failed to parse schema {rel} ({label}): {exc}")

    check_schema_paths(minimal.get("requiredSchemas", []), "core-v4-minimal")
    for name, mod in modules.items():
        check_schema_paths(mod.get("requiredSchemas", []), f"module {name}")
        check_schema_paths(mod.get("experimentalSchemas", []), f"module {name} (experimental)")
    for profile in (modules_profile, federation):
        if profile.get("extendsProfileId") != "core-v4-minimal":
            errors.append(f"{profile['profileId']}: extendsProfileId must be core-v4-minimal")

    # 4) exact partition of the operation surface
    minimal_ops = list(minimal["requiredOperations"])
    module_ops = [op for mod in modules.values() for op in mod["requiredOperations"]]
    experimental_ops = [op for mod in modules.values()
                        for op in mod.get("experimentalOperations", [])]
    combined = minimal_ops + module_ops + experimental_ops
    if len(combined) != len(set(combined)):
        errors.append("Operation partition contains duplicates")
    if set(combined) != ops_v4:
        errors.append(f"Operation partition mismatch vs v4 OpenAPI: {sorted(set(combined) ^ ops_v4)}")

    # 5) federation levels reference defined modules
    for level, spec in federation["conformanceLevels"].items():
        for mod_name in spec["modules"]:
            if mod_name not in modules:
                errors.append(f"federation-v4 {level} references unknown module: {mod_name}")
        if spec.get("evidenceClass") not in (
                "reference", "local-live", "scheduler-live", "fleet-live", "cross-org-live"):
            errors.append(f"federation-v4 {level}: unknown evidenceClass")

    # 6) v4 fixtures validate against v4 / companion schemas
    schemas_by_id, schemas_by_path = _collect_store()
    direct_mappings = {
        "run-paused.response.json": SCHEMAS_V4 / "run.schema.json",
        "agent-message-run-correlated.request.json": SCHEMAS_V4 / "agent-message.schema.json",
        "handoff-attenuated.request.json": SCHEMAS_V4 / "handoff.schema.json",
        "execution-context-instrument.request.json": SCHEMAS_V4 / "execution-context.schema.json",
        "execution-context-analysis.request.json": SCHEMAS_V4 / "execution-context.schema.json",
        "journal-message-expired.event.json": SCHEMAS_V4 / "journal-envelope-event.schema.json",
    }
    for fixture_name, schema_path in direct_mappings.items():
        fixture_path = FIXTURES_V4 / fixture_name
        if not fixture_path.exists():
            errors.append(f"Missing fixture: {fixture_path}")
            continue
        try:
            fixture = v3._read_json(fixture_path)
            schema = v3._read_json(schema_path)
            errors.extend(
                v3._validate_instance(
                    fixture, schema, schema_path.resolve(), str(fixture_path),
                    schemas_by_id, schemas_by_path,
                )
            )
        except Exception as exc:
            errors.append(f"Validation error for {fixture_path}: {exc}")

    # 7) loosenings are real: v4 fixtures must NOT satisfy the old v3 requirements
    negative_cases = {
        "agent-message-run-correlated.request.json":
            v3.SCHEMAS_COMMON / "agent-message.schema.json",
        "execution-context-instrument.request.json":
            v3.SCHEMAS_COMMON / "execution-context.schema.json",
    }
    for fixture_name, v3_schema_path in negative_cases.items():
        fixture_path = FIXTURES_V4 / fixture_name
        if not fixture_path.exists():
            continue
        fixture = v3._read_json(fixture_path)
        v3_schema = v3._read_json(v3_schema_path)
        failures = v3._validate_instance(
            fixture, v3_schema, v3_schema_path.resolve(), str(fixture_path),
            schemas_by_id, schemas_by_path,
        )
        if not failures:
            errors.append(
                f"{fixture_name} unexpectedly passes the v3 schema — "
                f"loosening in v4 variant of {v3_schema_path.name} is not effective"
            )

    # 8) deep constraint checks the v3 engine skips: pattern, const, if/then
    import re as _re

    def _resolve(schema, path):
        if "$ref" in schema:
            target = (path.parent / schema["$ref"]).resolve()
            return v3._read_json(target), target
        return schema, path

    def _deep_ok(instance, schema, path, trail):
        schema, path = _resolve(schema, path)
        errs = []
        for sub in schema.get("allOf", []):
            errs += _deep_ok(instance, sub, path, trail)
        if "if" in schema:
            if _if_matches(instance, schema["if"], path):
                then = schema.get("then")
                if then:
                    errs += _required_errs(instance, then, trail)
                    errs += _deep_ok(instance, then, path, trail)
        if "oneOf" in schema:
            # accept if any branch deep-checks clean AND basic-validates
            branch_errs = []
            ok = False
            for sub in schema["oneOf"]:
                sub_r, sub_p = _resolve(sub, path)
                be = v3._validate_instance(instance, sub_r, sub_p, trail, schemas_by_id, schemas_by_path)
                de = _deep_ok(instance, sub_r, sub_p, trail)
                if not be and not de:
                    ok = True
                    break
                branch_errs += be + de
            if not ok:
                errs.append(f"{trail}: no oneOf branch satisfies deep constraints")
        if isinstance(instance, dict):
            if "const" in schema and instance != schema["const"]:
                errs.append(f"{trail}: const mismatch")
            for key, sub in schema.get("properties", {}).items():
                if key in instance:
                    errs += _deep_ok(instance[key], sub, path, f"{trail}.{key}")
        elif isinstance(instance, list):
            items = schema.get("items")
            if items:
                for i, el in enumerate(instance):
                    errs += _deep_ok(el, items, path, f"{trail}[{i}]")
        elif isinstance(instance, str):
            pat = schema.get("pattern")
            if pat and not _re.fullmatch(pat, instance):
                errs.append(f"{trail}: '{instance[:40]}' does not match pattern {pat}")
            if "const" in schema and instance != schema["const"]:
                errs.append(f"{trail}: const mismatch")
        else:
            if "const" in schema and instance != schema["const"]:
                errs.append(f"{trail}: const mismatch")
        return errs

    def _if_matches(instance, cond, path):
        cond, path = _resolve(cond, path)
        if not isinstance(instance, dict):
            return False
        for req in cond.get("required", []):
            if req not in instance:
                return False
        for key, sub in cond.get("properties", {}).items():
            if key in instance:
                sub, _ = _resolve(sub, path)
                if "const" in sub and instance[key] != sub["const"]:
                    return False
        return True

    def _required_errs(instance, then, trail):
        errs = []
        if isinstance(instance, dict):
            for req in then.get("required", []):
                if req not in instance:
                    errs.append(f"{trail}: conditional requires '{req}'")
        return errs

    for fixture_name, schema_path in direct_mappings.items():
        fixture_path = FIXTURES_V4 / fixture_name
        if not fixture_path.exists() or not schema_path.exists():
            continue
        errors.extend(_deep_ok(v3._read_json(fixture_path), v3._read_json(schema_path),
                               schema_path.resolve(), fixture_name))

    # 9) conditional/negative checks: deliberately broken variants must fail
    run_fx = v3._read_json(FIXTURES_V4 / "run-paused.response.json")
    broken = dict(run_fx); broken.pop("workflowState", None)
    if not _deep_ok(broken, v3._read_json(SCHEMAS_V4 / "run.schema.json"),
                    (SCHEMAS_V4 / "run.schema.json").resolve(), "run-paused-minus-workflowState"):
        errors.append("paused run without workflowState unexpectedly passes the v4 run schema")

    ec_fx = v3._read_json(FIXTURES_V4 / "execution-context-analysis.request.json")
    broken = dict(ec_fx); broken.pop("dataVersion", None)
    if not _deep_ok(broken, v3._read_json(SCHEMAS_V4 / "execution-context.schema.json"),
                    (SCHEMAS_V4 / "execution-context.schema.json").resolve(), "analysis-minus-dataVersion"):
        errors.append("analysis context without dataVersion unexpectedly passes the v4 schema")

    jm = v3._read_json(FIXTURES_V4 / "journal-message-expired.event.json")
    v3_journal = CONTRACTS / "schemas" / "events" / "journal-envelope-event.schema.json"
    if not v3._validate_instance(jm, v3._read_json(v3_journal), v3_journal.resolve(),
                                 "journal-expired-vs-v3", schemas_by_id, schemas_by_path):
        errors.append("journal.message.expired unexpectedly passes the v3 journal schema "
                      "— the new eventType should only be reachable via the v4 envelope")

    if errors:
        print("v4 contract validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(
        "v4 contract validation OK: "
        f"{len(ops_v4)} operations ({len(minimal_ops)} minimal, {len(module_ops)} module, "
        f"{len(experimental_ops)} experimental), {len(modules)} modules, "
        f"{len(federation['conformanceLevels'])} conformance levels, "
        f"{len(direct_mappings)} fixtures validated (deep pattern/conditional checks on), "
        f"{len(negative_cases) + 3} negative checks passed"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

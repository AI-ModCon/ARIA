# ARIA

**ARIA** = **AI Research Infrastructure Architecture**

Canonical **GMP core-v3** contracts (OpenAPI 3.1, JSON Schemas, conformance profiles, fixtures, and validation tooling) live under [`contracts/`](contracts/README.md).

This repository was formerly named **`GM_API_Specification`**; bookmarks and remotes should use `https://github.com/brettin/ARIA.git` after the GitHub rename.

## Quick links

- [contracts/README.md](contracts/README.md) — spine charter and API surface
- [contracts/openapi/gmp-core-v3.yaml](contracts/openapi/gmp-core-v3.yaml) — OpenAPI document
- [scripts/validate_v3_contracts.py](scripts/validate_v3_contracts.py) — contract validator

## Validation

```bash
make validate-v3-contracts
```

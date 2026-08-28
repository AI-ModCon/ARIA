# ARIA

**ARIA** = **AI Research Infrastructure Architecture**

Canonical **GMP core-v3** contracts (OpenAPI 3.1, JSON Schemas, conformance profiles, fixtures, and validation tooling) live under [`contracts/`](contracts/README.md).

This repository was formerly named **`GM_API_Specification`**; bookmarks and remotes should use `https://github.com/AI-ModCon/ARIA.git` after the GitHub rename.

## Quick links

- [contracts/README.md](contracts/README.md) — spine charter and API surface
- [contracts/openapi/gmp-core-v3.yaml](contracts/openapi/gmp-core-v3.yaml) — OpenAPI document
- [scripts/validate_v3_contracts.py](scripts/validate_v3_contracts.py) — contract validator

## Validation

```bash
make validate-v3-contracts
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to report issues, propose RFCs, and submit pull requests.

## License

This project is licensed under the Apache License 2.0 — see the [LICENSE](LICENSE) file for details.

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Support

This project acknowledges support from the U.S. Department of Energy's Genesis Mission.

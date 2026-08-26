# Contributing to ARIA

Thank you for your interest in contributing to ARIA! This document provides guidelines and instructions for contributing to this project.

ARIA holds the canonical **GMP core-v3** contracts (OpenAPI, JSON Schemas, conformance profiles, fixtures, and validation tooling). Most changes belong under [`contracts/`](contracts/README.md).

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](./CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you do not need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps which reproduce the problem**
- **Provide specific examples to demonstrate the steps** (schema paths, OpenAPI operation IDs, fixture files)
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include your environment details** (OS, Python version used to run the validator)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and the proposed behavior**
- **Explain why this enhancement would be useful**

Contract-surface changes (new operations, schema fields, or breaking semantics) should go through the [RFC process](contracts/rfcs/README.md): open one PR per RFC, then a follow-up PR for the implementation.

### Pull Requests

- Follow the style guidelines below
- Document new contract surfaces in the relevant README, RFC, or governance notes
- End all files with a newline
- Avoid platform-dependent code in validation tooling
- Add or update fixtures for any new or changed schema
- Include appropriate commit messages

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/AI-ModCon/ARIA.git`
3. Create a new branch: `git checkout -b feature/my-feature`
4. Make your changes under `contracts/` (or `scripts/` for the validator)
5. Validate contracts:
   ```bash
   make validate-v3-contracts
   ```
6. Commit your changes: `git commit -am "Add my feature"`
7. Push to the branch: `git push origin feature/my-feature`
8. Submit a pull request

For RFC drafts, see [`contracts/rfcs/README.md`](contracts/rfcs/README.md). Open one PR per RFC.

## Style Guidelines

### Contracts (OpenAPI, JSON Schema, fixtures)

- Keep OpenAPI 3.1 documents and JSON Schemas valid and internally consistent (`$ref` paths must resolve)
- Prefer additive, optional fields for minor contract changes; breaking changes require a new major API path (see [`contracts/v3-release-governance.md`](contracts/v3-release-governance.md))
- Add machine-validated fixtures under `contracts/fixtures/` for new or changed payloads
- Use Markdown for documentation and RFCs

### Python (validator)

The contract validator in `scripts/validate_v3_contracts.py` is stdlib-only Python 3. When changing it:

- Use [PEP 8](https://www.python.org/dev/peps/pep-0008/) as the coding standard
- Use type hints where appropriate
- Keep the script dependency-free unless there is a strong reason to add a package

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Documentation

- Use Markdown for documentation
- Keep documentation up-to-date with contract changes
- Write clear, concise documentation
- Include examples (fixtures or YAML snippets) where appropriate

## Testing

- Run `make validate-v3-contracts` before submitting a pull request
- Add or update fixtures so new schemas and operations are covered
- Ensure all existing fixtures continue to pass

## Guidelines for AI/LLM-Assisted Contributions

- **Remain accountable for all your outputs and decisions.**
   Individuals remain fully responsible and accountable for the accuracy, quality, appropriateness, and consequences of their work. Use of AI does not transfer this responsibility to the AI model, agent, or other tool.
- **Understand your work.**
   Regardless of how code or PR was produced, this project requires that authors illustrate a thorough understanding of any proposed changes. You must review such code line-by-line; it is your responsibility to ensure that it is correct, and that it does not breach copyright. Always critically engage with AI outputs, do not trust them implicitly. AI-assisted code, analysis, and artifacts must be tested and validated at a level appropriate to their impact. Authors are responsible for ensuring that generated code is correct, secure, maintainable, non-obfuscated, appropriately scoped, documented, and reproducible where relevant.
- **Disclose AI-generated or AI-assisted work.**
   If AI/LLM tools were primarily used to generate code or artifacts, this should be clearly indicated in the PR.
- **Use of AI to review PRs.**
   All PRs must be reviewed by a human reviewer. An LLM review may be used in addition to a human reviewer since this can help spot issues that a human may have missed, but this should not be the sole reviewer. The human reviewer should be fully accountable and responsible for the review feedback or comments (see 1).
- **Proprietary or personal information.**
   For this project, proprietary or personal information should never be sent to code generators or AI tools.
- **Be transparent, assume goodwill, and share what you learn.**
   Contributors should be open about relevant AI use, disclose details of AI use as appropriate to the project, engage constructively with colleagues, and share experiences and lessons learned with the project.

## Questions?

Feel free to open an issue with the label `question` if you have any questions.

Thank you for contributing!

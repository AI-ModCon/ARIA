# RFC 001: Run invocation I/O and MAG tool_calls

## Problem

core-v3 `execution-context.schema.json` describes reproducibility hashes only. Platform v0 sends `inputs` (messages, tools, prompt) and `parameters` (model, system) and returns `outputs.tool_calls` as `[{ id, name, input }]`.

## Proposal

- Add companion schema `run-invocation.schema.json` OR extend profile with `x-gmp` invocation block.
- Document OpenAI/Anthropic interop and MAG normalization.

## Platform reference

[ARIAPlatform `platform-v0-implementation-profile.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/platform-v0-implementation-profile.json) — `ExecutionContextSubmit`, `MagToolCall`, `RunOutputs`.

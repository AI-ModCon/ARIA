# RunInvocation interop & MAG normalization

Implements [RFC 001 — Run invocation I/O and MAG `tool_calls`](../rfcs/001-run-invocation-and-tool-use.md).

The spine [`execution-context.schema.json`](../schemas/common/execution-context.schema.json) records reproducibility hashes only. Platform v0 additionally sends literal `inputs` (messages, tools, prompt) and `parameters` (model, system) and returns `outputs.tool_calls`. The optional companion [`RunInvocation`](schemas/run-invocation.schema.json) artefact captures that literal request/response payload **without widening the mandatory spine**. Orchestrators that only emit hashes can ignore it; deployments that need to persist or exchange the verbatim invocation reference it by `contextHash`.

This document defines how the Model/Agent Gateway (MAG) **normalizes** provider-specific OpenAI and Anthropic shapes into the single `RunInvocation` representation.

## Canonical shape

```jsonc
{
  "contextHash": "<ties to spine ExecutionContext>",
  "inputs":     { "model", "system", "messages": [{ "role", "content" }], "tools": [{ "name", "description", "input_schema" }] },
  "parameters": { "model", "system", "temperature", "max_tokens", ... },
  "outputs":    { "content", "tool_calls": [{ "id", "name", "input" }], "usage", "finish_reason", "model", "provider" }
}
```

The normative element is `outputs.tool_calls` as an array of `{ id, name, input }` (MAG `MagToolCall`), where `input` is the **decoded** arguments object.

## Messages (`inputs.messages`)

| Concept | OpenAI | Anthropic | RunInvocation (normalized) |
| --- | --- | --- | --- |
| Roles | `system`, `user`, `assistant`, `tool` | `user`, `assistant` (+ top-level `system`) | `system`, `user`, `assistant`, `tool` |
| System prompt | `messages[0]` with `role:"system"` | top-level `system` string | `inputs.system` / `parameters.system`, and/or a `role:"system"` message |
| Content | `content` string, or content parts | `content` string, or content blocks | string **or** list of typed blocks |
| Tool result | `role:"tool"` + `tool_call_id` | `user` message w/ `tool_result` block (`tool_use_id`) | `role:"tool"` + `tool_call_id` |

## Tools (`inputs.tools`)

| Field | OpenAI | Anthropic | RunInvocation |
| --- | --- | --- | --- |
| Name | `function.name` | `name` | `name` |
| Description | `function.description` | `description` | `description` |
| Args schema | `function.parameters` | `input_schema` | `input_schema` |

OpenAI's `function.parameters` is renamed to `input_schema` on normalization.

## Tool calls (`outputs.tool_calls`)

| Field | OpenAI | Anthropic | RunInvocation |
| --- | --- | --- | --- |
| Id | `tool_calls[].id` | `tool_use` block `id` | `id` |
| Name | `tool_calls[].function.name` | `tool_use` block `name` | `name` |
| Arguments | `tool_calls[].function.arguments` (**JSON string**) | `tool_use` block `input` (**object**) | `input` (**object**) |

Normalization rules:

1. **Parse arguments.** OpenAI `function.arguments` is a JSON-encoded string; MAG parses it into the `input` object. Anthropic `input` is already an object and is passed through.
2. **Preserve ids.** `id` is retained so a later `role:"tool"` result can reference it via `tool_call_id`.
3. **Validate names.** Each `tool_calls[].name` should match a `inputs.tools[].name`.
4. **`finish_reason`.** OpenAI `finish_reason:"tool_calls"` and Anthropic `stop_reason:"tool_use"` both normalize to a stop indicating tool use.

## `maxToolCalls` semantics

Budget enforcement counts **model-returned `tool_calls` batches per MAG invoke** — i.e. `len(outputs.tool_calls)` — not local tool-agent executions. See the platform [`platform-v0-implementation-profile.json`](https://github.com/brettin/ARIAPlatform_v0/blob/main/reference/platform-v0-implementation-profile.json) `semantics.maxToolCalls`.

## Spine linkage

`RunInvocation.contextHash` ties back to a spine [`Run.executionContext`](../schemas/common/run.schema.json). When a single canonical hash is used it equals `ExecutionContext.configHash`; otherwise it is an opaque digest agreed by orchestrator and platform. The spine `Run` is intentionally **not** widened — `RunInvocation` stays companion/optional, consistent with [`profiles/core-v3-companion.json`](../profiles/core-v3-companion.json).

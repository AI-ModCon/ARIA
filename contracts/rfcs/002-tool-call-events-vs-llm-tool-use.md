# RFC 002: tool.call events vs LLM tool-use

## Status

**Implemented.** The normative substance of this RFC has already been addressed in `main` by PR #9 ("Tighten RunInvocation companion contract"). This document is retained as a historical / design-rationale record.

- Event-semantics clarification (model turn vs executed tool) landed in `contracts/companion/run-invocation-interop.md`, which now states that a `RunInvocation` records MAG/model turns while executed-tool telemetry remains in the event stream, with tool results appearing as later `role:"tool"` messages linked by `tool_call_id`.
- Budget-field alignment (`maxToolCalls`) landed in the same file: the `## maxToolCalls semantics` section was rewritten from "model-returned `tool_calls` batches per MAG invoke" to "model-returned tool call items per MAG invoke", matching the metering behavior described below.

## Problem

- Spec `tool-call-event` is audit telemetry (`toolName`, `status`, `latencyMs`, `tokenCost`).
- Platform `run.outputs.tool_calls` is model-requested function calls.
- `maxToolCalls` on budgets: platform counts MAG-returned batches per run, not local agent execution.

## Proposal

- Clarify event semantics (model turn vs executed tool).
- Align budget field documentation with metering behavior.

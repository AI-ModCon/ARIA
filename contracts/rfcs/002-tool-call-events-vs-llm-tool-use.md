# RFC 002: tool.call events vs LLM tool-use

## Problem

- Spec `tool-call-event` is audit telemetry (`toolName`, `status`, `latencyMs`, `tokenCost`).
- Platform `run.outputs.tool_calls` is model-requested function calls.
- `maxToolCalls` on budgets: platform counts MAG-returned batches per run, not local agent execution.

## Proposal

- Clarify event semantics (model turn vs executed tool).
- Align budget field documentation with metering behavior.

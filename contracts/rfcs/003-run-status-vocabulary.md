# RFC 003: Run status vocabulary

## Problem

Spec: `queued`, `running`, `succeeded`, `failed`, `cancelled`. Platform: `pending`, `planning`, `running`, `paused`, `completed`, `failed`, `cancelled`.

## Proposal

Add `completed` as alias of `succeeded` or adopt platform enum with mapping table in profile.

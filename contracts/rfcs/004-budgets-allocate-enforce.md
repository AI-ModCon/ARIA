# RFC 004: Budget allocate and enforce

## Problem

- Spec `BudgetPolicy` used for both request and response with client-supplied `budgetId`.
- Platform allocate: server-generated `budgetId`, `ttlSeconds`, `maxCostUsd`, usage counters on response.
- Spec `enforceBudget` uses tier `ModelRoutingPolicy`; platform uses `budgetId` + `fallbackModel`.

## Proposal

Split allocate request/response schemas; document enforce operation for budget-bound routing.

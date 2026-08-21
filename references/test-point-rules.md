# Test-point rules

Generate P0 for the core user or service path and for blocker findings. Generate P1 for boundary, exception, important combinations, and historical-defect regression. Generate P2 for permission, compatibility, environment, and low-frequency scenarios.

Cover these types whenever the input applies: `happy_path`, `negative`, `boundary`, `exception`, `combination`, `regression`, `permission`, `consistency`, `compatibility`.

For OpenAPI, include required/missing/invalid values, enum and bounds, documented responses, security, idempotency where applicable, and dependent endpoint sequences. For source code, derive only from observed branches and failure handling. For defects, retain the page or record reference on the point and case.

Use `awaiting_confirmation` or `skipped` for unresolved findings. Never silently discard them.

## Business-first derivation and de-duplication

Describe every test point first as a business outcome: actor or data dimension, trigger, and observable result. Use code only as supporting evidence for the scope, branch, error handling, or data source; do not make a line-level condition a separate test point when it verifies the same business outcome.

Before publishing test points, group candidates by the same business object, data dimension, trigger, and expected result. Merge candidates in the same group into one point; retain all Jira/code references and list them under `derivation_reason`. Keep separate points only when a user can prepare different data or observe a materially different business result.

Treat a source-code guard as a defensive implementation detail unless evidence shows that the guarded input is reachable in the business data model. If the business model rules the input out, test the upstream data-routing rule or merge it into the primary business test; do not create an impossible negative scenario.

Classify an item discovered only by keyword or topical similarity as `skipped` unless its description and verified code path establish a causal relation to the current change. Record the exclusion reason, such as “test-data issue” or “no direct call-chain evidence.”

## Human-review language

Present human-review materials in the reviewer’s language. When the reviewer uses Chinese, do not expose English field labels, enum values, or implementation-oriented metadata such as `coverage_type`, `source_type`, `source_reference`, `expected_focus`, or `status`.

Preserve the analysis elements using plain Chinese labels: 测试点、优先级、测试类型、来源及依据、推导原因、验证内容、评审状态。 Keep code identifiers only where they are necessary as evidence, and explain their business meaning in the same item.

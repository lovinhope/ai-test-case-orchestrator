---
name: ai-test-case-generator
description: Generate traceable candidate manual test cases for one verified Git commit from confirmed test points, with optional run-scoped test-data preparation through a configured non-production test database. Use after human confirmation and historical-case association; never generate automation code or mix commits.
---

# Commit manual cases

Read [case-schema.md](references/case-schema.md), [test-data-contract.md](references/test-data-contract.md), and the parent [interaction-contract.md](../references/interaction-contract.md), including their test-case quality rules, the matching test points, association, and challenge artifacts. Run `scripts/generate_test_cases.py` to verify commit identity and that points are confirmed. Before cases, query and read the configured historical manual-case/defect knowledge base and write `04-historical-case-association.md`.

When a case needs concrete records, use the test-database workflow in `test-data-contract.md`: read the local test-database configuration, verify the target is non-production, inspect reference data, prepare a run-scoped data plan, and—only when the current request explicitly authorizes creation—write and verify data through the configured Lowrisk data-mock adapter or a reviewed database adapter. Persist `04-test-data-manifest.md`, link each dataset to its case number, and include the manifest in the case preconditions. If creation cannot be verified, keep the dataset `待准备` and do not claim the case is executable.

Then write candidate `04-test-cases.md`; every case is `pending_human_review`, traceable to a point and the single commit, and includes a linked task/requirement URL, requirement explanation, unique number, purpose, preconditions, numbered steps, matching expected results, priority, and actionable evidence. Apply the quality gate in `case-schema.md` before presenting cases for human review. The reviewer-facing page must provide editable review inputs and a submit-case-review action that records adopted, modified, or discarded per-case decisions. Do not mark cases adopted automatically.

If points are pending, stop. If evidence is unavailable, record the block; do not invent expected results.

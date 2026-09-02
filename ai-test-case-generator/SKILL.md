---
name: ai-test-case-generator
description: Generate traceable candidate manual test cases from exactly one confirmed product requirement (Jira link or requirement document) and confirmed test points. A Git Commit is optional supplementary implementation evidence. Use after human confirmation and historical-case association; never generate automation code or mix commits.
---

# Manual test-case generation

Read [case-schema.md](references/case-schema.md) and [test-data-contract.md](references/test-data-contract.md), including their test-case quality rules, the matching test points, association, and challenge artifacts. The only primary input is one confirmed requirement supplied as a Jira link or requirement document; a verified commit is optional implementation evidence and must not replace the requirement. Run `scripts/generate_test_cases.py` to verify the requirement identity and that points are confirmed.

The generation artifact `04-test-cases.md` is a normal Markdown document organized around one task. Follow `case-schema.md` for its task-level metadata fields, test-point-to-case relationship, traceability fields, quality rules, statuses, and human-facing language. Put `测试用例`、`相关JIRA`、`相关业务`、`相关模块`、`相关表`、`相关配置`、`相关接口`、`相关定时任务`、`相关权限控制` in the task header; do not repeat them in every case. Each confirmed test point expands into actual cases such as `TC01` and `TC02`. Do not read, require, or imitate the Confluence `test_case_template` when generating this local Markdown artifact; template lookup must not block case generation.

Before cases, query and read the configured historical manual-case/defect knowledge base and write `04-historical-case-association.md`.

When a case needs concrete records, use the test-database workflow in `test-data-contract.md`: read the local test-database configuration, verify the target is non-production, inspect reference data, prepare a run-scoped data plan, and—only when the current request explicitly authorizes creation—write and verify data through the configured Lowrisk data-mock adapter or a reviewed database adapter. Persist `04-test-data-manifest.md`, link each dataset to its case number, and include the manifest in the case preconditions. If creation cannot be verified, keep the dataset `待准备` and do not claim the case is executable.

Then write candidate `04-test-cases.md` according to `case-schema.md`, without applying a Confluence template. Write the task metadata once, then expand the confirmed test points into `TC01`, `TC02`, and subsequent actual cases. Every case starts with `review_status: awaiting_confirmation` and `case_status: candidate`, is traceable to its test point and requirement, and includes optional implementation evidence where available. Apply the quality gate in `case-schema.md` before presenting cases for human review. Record the human review decision in `05-case-human-review.md`, including adopted, modified, or discarded per-case decisions. Do not mark cases adopted automatically.

When a case is modified, delete the old revision and create a new `generation_id`/revision under `revisions/<revision>/04-test-cases.md`, reference the superseded revision, and assign new case IDs. Do not keep the old revision as an active artifact. Unmodified adopted/discarded history may remain for traceability.

Only after a case is explicitly adopted or modified and approved for delivery may it be pushed to Confluence. Build the published content from the configured `[test_case_template]` page, not from the local default schema alone, and publish it under the configured `[test_case_publish]` space and `menu_id`. Preserve the template's structure and field order; do not publish pending or discarded cases. Record the destination space, menu id, published case numbers, and publish result in the delivery artifact.

Before drafting a case, explicitly decide whether it requires test data. For every database-backed case, derive the required data from the implementation and call chain, including actual tables/entities, joins, filters, caches, enums, statuses, dates, scopes, and dependent records. Use the smallest complete verified dataset; never invent codes, statuses, fields, or foreign keys. If a required value or table cannot be verified, record the blocker and leave the dataset `待准备`.

When publishing cases to Confluence, use `scripts/publish_test_cases.py` only after local validation and human review pass. Read the destination from the configured publish settings and the Confluence credentials from `TASKFLOW_CONFIG_PATH`; never store or print credentials. Use the configured `test_case_template` to render the published content, exclude discarded cases, and record the publish result in `07-delivery.md`. Support `--dry-run` before any external write.

If points are pending, stop. If evidence is unavailable, record the block; do not invent expected results.

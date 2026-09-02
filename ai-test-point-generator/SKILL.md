---
name: ai-test-point-generator
description: Generate traceable manual test points from one requirement's association and challenge artifacts, with an optional supplementary Git Commit. Use after challenge review; pause for human confirmation before case generation.
---

# Commit test points

Read [test-point-rules.md](references/test-point-rules.md), the matching `01-association.md`, and `02-review.md`, including the systematic coverage method. Run `scripts/generate_test_points.py` to verify the optional `commit_id` when supplied and scaffold `03-test-points.md`. Decompose the confirmed requirement and evidence into traceable rules, apply the scenario-dimension checklist and appropriate test-design models, record requirement-to-point traceability, prioritize depth by risk, and perform the reverse coverage review before presenting points. Convert confirmed rules and optional verified commit behavior into business-outcome test points; include happy path, negative, boundary, exception, permission, consistency, compatibility, and historical regression where applicable. Record human corrections or additions in the Markdown artifact and wait for explicit confirmation before continuing. Keep unresolved items as `awaiting_confirmation` or `skipped` with reasons.

Test-point generation uses explicit modification revisions. When a reviewer chooses “修改”, delete the old revision and create a new `generation_id`/revision under `revisions/<revision>/03-test-points.md`, reference the superseded challenge/point revision, and assign new point IDs. Do not silently rewrite a prior point without an explicit modification decision.

In `03-test-points.md`, include a `测试点确认清单` section before the detailed test-point sections. The checklist must use this Markdown table format and contain every generated test point:

```markdown
## 测试点确认清单

| 编号 | 测试点 | 状态 |
|---|---|---|
| TP01 | 示例测试点 | 待确认 |
```

The `状态` value must reflect the current human-review state, such as `待确认`、`已确认`、`已修改`、`已新增`、`已跳过` or `待补充`. Keep the checklist synchronized with the detailed test-point content and update it when a reviewer adds or changes a point.

Set `status: pending_confirmation` and stop. Never generate `04-test-cases.md` in this stage. Human changes must be recorded without changing the commit identity or the original point state graph.

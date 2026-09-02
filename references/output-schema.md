# Output schema

Use Markdown artifacts with UTF-8 encoding. Treat each case directory as one task. `00-input.md` records one task object containing `测试用例`, `相关JIRA`, `相关业务`, `相关模块` (optional), `相关表`, `相关配置` (optional), `相关接口` (optional), `相关定时任务` (optional), and `相关权限控制` (optional), together with `generation_mode`, `source_type`, `source_reference`, `prompt_version`, and `rule_version`. Record a `generation_id`/revision for every challenge, test-point, and case generation. `01-association.md` records the Jira/Confluence script path and command mapping, query scope, query time, result status, and Confluence/Jira evidence.

Use this task header followed by the case shape in `04-test-cases.md`:

```markdown
## 任务信息
- 测试用例: <task name>
- 相关JIRA: <issue key or URL>
- 相关业务: <business scope>
- 相关模块: <optional>
- 相关表: <tables or 不涉及>
- 相关配置: <optional>
- 相关接口: <optional>
- 相关定时任务: <optional>
- 相关权限控制: <optional>

## TC01 Title
- priority: P0
- test_point: TP01
- source_type: requirement | openapi | source_code | historical_defect | business_profile
- source_reference: concrete path, endpoint, commit, or record
- coverage_type: happy_path | negative | boundary | exception | combination | regression | permission | consistency | compatibility
- review_status: confirmed | awaiting_confirmation
- case_status: candidate | adopted | modified | discarded
- historical_defect_reference: page title + URL/page id + update time  # required for regression
- jira_reference: issue key + URL + update time  # required when Jira is the source
- preconditions:
  - actionable condition
- steps:
  1. concrete action
- expected_results:
  1. observable result for step 1
```

Use `03-test-points.md` with `status: pending_confirmation` until a human approves it. Record each P0 point and each unresolved rule explicitly. The document must include this confirmation checklist, containing every test point:

```markdown
## 测试点确认清单

| 编号 | 测试点 | 状态 |
|---|---|---|
| TP01 | ... | 待确认 |
```

Keep the checklist synchronized with the detailed test-point sections and reviewer changes.

## Chinese human-delivery schema

When the requester uses Chinese, write `04-test-cases.md` with Chinese task-header and case field labels while preserving every element in the case shape above. Use task fields: 测试用例、相关JIRA、相关业务、相关模块、相关表、相关配置、相关接口、相关定时任务、相关权限控制. Use case fields: 用例、优先级、测试点、来源类型、来源及依据、覆盖类型、评审状态、用例状态、历史缺陷依据、需求依据、前置条件、测试步骤、预期结果. Use Chinese status and coverage values. Do not expose English metadata or implementation class names in the human-delivery document; retain them only in association/review evidence artifacts.

Generated cases are candidates, not adopted cases. Use `用例状态：待人工评审` until `05-case-human-review.md` records an explicit human decision. Before creating `04-test-cases.md`, write `04-historical-case-association.md` from read Confluence historical-case evidence; retain the Confluence title, URL/page id, update time, match reason, and coverage decision.

When a reviewer chooses “修改”, delete the old revision, write the modified artifacts below `revisions/<revision>/`, and retain an explicit supersession link with new IDs. Do not silently rewrite an old revision without that decision.

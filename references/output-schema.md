# Output schema

Use Markdown artifacts with UTF-8 encoding. `00-input.md` records `generation_mode`, `source_type`, `source_reference`, `prompt_version`, and `rule_version`. `01-association.md` records the Jira/Confluence script path and command mapping, query scope, query time, result status, and Confluence/Jira evidence.

Use this case shape in `04-test-cases.md`:

```markdown
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

Use `03-test-points.md` with `status: pending_confirmation` until a human approves it. Record each P0 point and each unresolved rule explicitly.

## Chinese human-delivery schema

When the requester uses Chinese, write `04-test-cases.md` with Chinese field labels while preserving every element in the case shape above. Use: 用例、优先级、测试点、来源类型、来源及依据、覆盖类型、评审状态、用例状态、历史缺陷依据、需求依据、前置条件、测试步骤、预期结果. Use Chinese status and coverage values. Do not expose English metadata or implementation class names in the human-delivery document; retain them only in association/review evidence artifacts.

Generated cases are candidates, not adopted cases. Use `用例状态：待人工评审` until `05-case-human-review.md` records an explicit human decision. Before creating `04-test-cases.md`, write `04-historical-case-association.md` from read Confluence historical-case evidence; retain the Confluence title, URL/page id, update time, match reason, and coverage decision.

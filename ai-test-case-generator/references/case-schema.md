# Candidate case schema

This schema is the human-facing format authority for the local Markdown artifact `04-test-cases.md`. The artifact is not generated from or constrained by the Confluence `test_case_template`; a missing or unreadable Confluence template must not block generation. The schema must retain the requirement source, test-point traceability, priority, preconditions, executable steps, one-to-one expected results, review status, and candidate status.

## Task-level metadata

The Markdown document is organized around one task. Put the following shared fields once in the task header (for example, in `任务信息`), not inside every `TC<NN>`:

| Field | Required | Meaning |
|---|---|---|
| 测试用例 | yes | Task name or test-case task title |
| 相关JIRA | yes when available | Jira issue key or URL associated with the task |
| 相关业务 | yes | Business domain or rule scope |
| 相关模块 | optional | Product/module scope |
| 相关表 | yes when applicable | Impacted or verified database tables |
| 相关配置 | optional | Configuration, feature flag, or parameter scope |
| 相关接口 | optional | Impacted or verified API/interface scope |
| 相关定时任务 | optional | Impacted or verified scheduled-job scope |
| 相关权限控制 | optional | Impacted role, permission, menu, or access-control scope |

Keep other shared task context, such as `commit_id`, source/evidence, and requirement references, at task level when it applies to the whole task. Do not duplicate task-level fields in each case unless a particular case has a materially different value; in that exception, label the case-specific override explicitly.

Each confirmed test point expands into one or more actual cases in this document. `TC01`, `TC02`, and subsequent IDs are test cases derived from test points, not additional task records. Each `TC<NN>` must include its linked `test_point`, priority, case objective, coverage type, preconditions, numbered steps, matching numbered expected results, `review_status: awaiting_confirmation`, and `case_status: candidate`. After human review, use `review_status: confirmed` and `case_status: adopted`, `modified`, or `discarded` as applicable. Include case-specific source/evidence when needed for traceability, and include the historical defect reference for regression cases. Unresolved rules remain `awaiting_confirmation` and cannot become final cases.

## Test-case quality rules

A good test case is not judged by length or count. It should find real defects at low execution cost, produce consistent conclusions across testers, and remain easy to repeat and maintain.

### 1. Traceable source

- Trace the case to a requirement, confirmed business rule, design/interface contract, source-code evidence, or historical defect.
- State clearly which function and risk the case verifies.
- Keep the Jira, commit, test-point, Confluence page, or historical-defect reference precise enough for another tester to locate.

### 2. Clear objective

- Each case should primarily verify one business objective or one tightly coupled risk.
- The title must state the test intent directly, such as “已过期产品不可申购”.
- Split unrelated objectives into separate cases instead of accumulating unrelated steps.

### 3. Complete preconditions

Specify the conditions required to execute the case without guesswork, including as applicable:

- user identity, role, and permissions;
- environment, feature flags, configuration, and dependency services;
- required data state, data ownership, status, and time/trading-date context;
- required prior setup or isolation/reset conditions.

### 4. Executable steps

- Number steps in a deterministic order.
- Describe concrete user/system actions and inputs, but avoid unnecessary narration.
- Do not use vague instructions such as “正常操作”, “检查一下”, or “观察是否正常”.
- A tester should be able to execute the case from the text alone, without relying on undocumented personal experience.

### 5. Verifiable expected results

- Expected results must be objective, observable, and pass/fail decidable.
- Match expected results to the numbered steps one-to-one; each step must have a corresponding expected result.
- Specify concrete evidence where relevant: page text or state, status transition, validation message, API response, database record, event, log, or permission boundary.
- Do not write only “系统正常”; state exactly what is displayed, changed, rejected, persisted, or left unchanged.

### 6. Risk-based coverage

Cover the important risks implied by the confirmed rules and evidence, prioritizing value over case count. Consider when applicable:

- normal flow;
- boundary values and state transitions;
- invalid or missing input/data;
- permissions and roles;
- duplicate submission, concurrency, timeout, retry, and dependency failure;
- compatibility and regression, including verified historical defects.

Do not invent unsupported scenarios. If a risk depends on an unresolved rule or unavailable evidence, keep it `awaiting_confirmation` or record the evidence block instead of turning it into a final case.

### 7. Independence and repeatability

- Cases should be independently executable; failure of one case must not be a hidden prerequisite for another.
- State explicit setup, cleanup, and reset requirements when data or workflow state can be changed.
- Repeated execution with the same controlled inputs should yield stable conclusions.
- Avoid relying on execution order, temporary data, or an unrecorded tester action.

### 8. Maintainability

- Keep each case focused and concise enough to update when requirements change.
- Reuse stable precondition descriptions and evidence references rather than duplicating unrelated detail.
- Make impacted business rules, test points, and source references easy to locate.

### 9. Defect-finding value

Each case must be able to distinguish a correct implementation from a meaningful incorrect implementation. Before accepting a case, ask:

- Which rule does it verify?
- What concrete defect would it detect?
- Can a tester execute it using only the documented preconditions and steps?
- Are the expected results specific enough to decide pass or fail?

Cases that would pass regardless of implementation, or that only restate “system works normally”, must be rewritten, merged, or removed.

### Quality gate before human review

Before writing `04-test-cases.md`, check that every candidate has:

- an explicit source and risk/functional objective;
- complete, reproducible preconditions;
- deterministic numbered steps;
- one-to-one, concrete expected results;
- appropriate risk coverage without unsupported assumptions;
- independence/repeatability and maintainability considerations;
- a plausible defect it could reveal;
- `review_status: awaiting_confirmation` and `case_status: candidate`.

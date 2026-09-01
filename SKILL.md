---
name: ai-test-case-orchestrator
description: Generate evidence-backed manual test cases from product requirements, API/interface definitions, source code, or historical defects. Route the input to the matching mode, associate Confluence/Jira/code knowledge, run one unified product/code challenge, obtain human approval for test points and cases, and evaluate coverage. Do not generate automation code.
---

# First-use credential preflight

Before any Jira, Confluence, or GitLab evidence query, check `TASKFLOW_CONFIG_PATH` and the required credentials. If the configuration is missing, remind the user to create the local user-level `lowrisk-jira.ini` described in `README.md` and stop before querying. Never ask the user to paste tokens into chat. If the configuration exists, reuse it without asking the user to log in or re-enter credentials.

# AI Test Case Orchestrator

## Human review modules

Read [interaction-contract.md](references/interaction-contract.md) for the conversational review protocol. The three review stages—产品/代码对抗、测试点审评、测试用例评审—must be handled directly in the Codex conversation. Keep the Markdown artifacts authoritative, show evidence and human-readable IDs such as E01/Q01/TP01/TC01, and do not advance a stage until the user explicitly confirms or supplies revisions. Do not generate HTML, CSS, JavaScript, review pages, or other UI artifacts.

Follow the flow below. Keep the stages separate and preserve traceability from input to final test cases. All stage artifacts use append-only revisions: confirmed or discarded challenge findings, test points, and test cases are immutable historical records. A regeneration creates a new `generation_id` under `revisions/<revision>/`, references the prior artifact, and never overwrites an original file, changes an original status, reuses an ID with a different meaning, or alters the original state graph.

## 1. Route the input

Select one or more applicable modes from the supplied evidence; do not require every input to be a Git commit.

| Input | Mode | Main focus |
|---|---|---|
| PRD, user story, Jira requirement, business rule | `requirement` | actors, rules, states, acceptance criteria |
| OpenAPI/Swagger JSON or YAML, API contract | `openapi` | paths, methods, parameters, enums, responses, security, idempotency |
| source files, repository, commit, diff | `source_code` | entry points, branches, exceptions, persistence, dependencies, transactions |
| defect record or historical-defect knowledge-base evidence | `historical_defect` | symptom, trigger, root cause, fix, regression |
| anonymized traffic or behavior aggregates | `business_profile` | frequency, unusual combinations, error distribution; supplemental only |

Record one task object in `00-input.md`, including `测试用例`, `相关JIRA`, `相关业务`, `相关模块` (optional), `相关表`, `相关配置` (optional), `相关接口` (optional), `相关定时任务` (optional), and `相关权限控制` (optional). Record `generation_mode`, `source_type`, `source_reference`, `prompt_version`, and `rule_version` there as task-level metadata. If multiple modes apply, record all of them and keep their evidence distinct.

## 2. Associate knowledge

Read the configured knowledge sources before designing tests:

1. Search and read Confluence business rules, related requirements, historical defects, and historical manual test cases.
2. Read the supplied Jira issue or requirement and any explicitly linked Jira issues.
3. For `source_code`, read the supplied source/diff or verified linked code. For `openapi`, read the complete contract.
4. For requirement or interface input, extract code clues from the read technical solution and Jira development links, then resolve them against a configured repository/Git service or supplied source path. Read the matched files, diff, or commit before retaining them as code evidence.
5. Rank evidence by relevance first, then update time. A title, search snippet, class name, method name, endpoint name, or table name alone is not code evidence.

When a relevant Confluence page is found, inspect its ancestors, parent index, linked child pages, and index entries. An indexed page does not need to be newly created or contain the supplied Jira key to be associated. Read the target page body before retaining it, and record the index/parent relationship as association evidence.

For interface and technical-solution association, search both business terms and implementation identifiers: feature names, permission-model terms, API paths, resource types, table names, service methods, and migration terms. Do not limit retrieval to the supplied Jira key or to the newest page.

Build three separate association lanes in `01-association.md`:

- **Business knowledge**: business rules, roles, permissions, states, acceptance criteria, and historical defects.
- **Technical solution**: architecture, interface contracts, data models, migration plans, permission models, and design decisions.
- **Related code**: verified source files, repository paths, commits, diffs, or Git service records that implement the input. A method name, endpoint, SQL fragment, table name, or class name found only in a document is a code clue, not verified code.

For requirement inputs, prioritize the current technical solution named by the requirement. Classify older interfaces, legacy role checks, and old SQL as `legacy_reference` or `compatibility_reference` when a newer framework or design supersedes them. Do not let legacy references become the main implementation evidence for a new-framework requirement. Retain both the classification and the reason.

When verified code is available, use the diff and changed call chain to derive the implemented change scope and intent clues: changed entry points, interfaces, fields, tables, branches, dependencies, and error handling. Record these as code-observed facts or code-derived intent, and compare them with the requirement. Do not ask the business to reconfirm a fact directly proved by the code; ask only for unresolved product intent, scope ownership, expected outcome, or acceptance criteria. If the code and requirement disagree, preserve the conflict for the 产品/代码对抗 review.

Carry verified code evidence forward from the association stage into the challenge and confirmation artifacts. Facts already proved by an associated commit, diff, source file, or call chain are automatically accepted as implementation scope and are not repeated as business confirmation items. Only code-versus-requirement conflicts or missing business intent proceed to confirmation.

For role and user scope, first derive the applicable users, roles, departments, permission tags, and existing page permissions from read business-knowledge pages and existing permission mappings. Only raise a confirmation item when the real user table, product table, role-to-user mapping, product-to-user mapping, or other required data is missing, inconsistent, or inaccessible. Mark the exact missing data and source table/page; do not ask the business to restate relationships already present in evidence.

For each page or entry point identified by the associated code change, derive a concrete permission inventory before asking for confirmation: menu, page, Tab, detail, button, API, Skill, product scope, strategy scope, page scope, role mapping, and special permission tags. The confirmation list must name the affected page/resource and ask which concrete products, strategies, menus, and special permissions apply; never use only generic questions such as “which users are affected?”.

Exclude weekly reports, QA weekly plans, release notes, test schedules, stand-up summaries, and other status-tracking pages from business or technical evidence unless the requester explicitly asks to analyze them. Do not use excluded pages to support association, challenge findings, test points, or cases.

Use the configured Jira/Confluence access layer only. For Jira-linked GitLab evidence, run the read-only `jira-code-read --issue <KEY>` command from `scripts/jira_confluence_use.py`; it reads Jira description/comments/remote links, resolves explicit GitLab commit and merge-request URLs through GitLab API, and returns verified metadata plus changed-file/diff summaries. Record business knowledge, technical solution, and code evidence in separate sections of `01-association.md`, including query scope, exact command or operation, timestamp, status, retained evidence, match reason, and evidence shortfalls. A connector, authentication, authorization, or configuration failure blocks evidence-backed generation; a successful zero-result search is recorded as `no_match` and may continue.

If code cannot be resolved or read, record `代码证据不可用` and keep code-related challenge findings as `待确认`; do not treat technical identifiers from a document as verified implementation behavior.

Do not expose credentials. Do not treat model inference, issue titles, branch names, or commit titles as verified behavior.

## 3. Run one unified product/code challenge

The challenge is one module named **产品/代码对抗**. Do not split it into separate product, code, and integration modules.

Use the associated business evidence and implementation/interface evidence together to challenge:

- requirement completeness: roles, permissions, states, boundaries, combinations, exceptions, and acceptance criteria;
- implementation or interface contract: entry point, input/output, validation, branches, dependencies, persistence, transaction, consistency, cache, idempotency, compatibility, and errors;
- requirement-to-implementation conflicts: mismatched fields, states, permission results, historical-data behavior, or response expectations;
- historical defect exposure: whether the current input can regress a verified prior defect.

Write `02-review.md` with findings under the single `产品/代码对抗` heading. Each finding must contain evidence, disposition, rationale, and source reference. Use `test_point`, `regression`, `awaiting_confirmation`, or `skipped`. If one evidence side is unavailable, state the shortfall and mark cross-side conclusions `awaiting_confirmation`; never invent expected results.

## 4. Human review gate for the challenge

Stop after `02-review.md` and request human review of the unified 产品/代码对抗.

In the conversation, show the associated business, technical, and verified-code evidence before the findings. Number questions as Q01, Q02, etc.; do not expose opaque evidence IDs as question labels. Ask the user to approve, modify, or reject each finding, persist the response in `02-review.md`, and only then hand off to test-point analysis. Record each response and disposition.

- If approved, continue to test-point and regression-point analysis.
- If rejected or modified, revise the association/challenge and repeat this gate.

Do not generate or publish test points before this challenge review is approved.

## 5. Analyze test points and regression points

Write `03-test-points.md` from the association and the unified challenge. Describe each point as a business outcome first: actor or data dimension, trigger, and observable result.

Cover applicable types: `happy_path`, `negative`, `boundary`, `exception`, `combination`, `regression`, `permission`, `consistency`, and `compatibility`.

Prioritize as follows:

- P0: core path or blocker;
- P1: boundary, exception, important combination, or historical-defect regression;
- P2: permission, compatibility, environment, and low-frequency coverage.

Merge points with the same business object, data dimension, trigger, and expected result. Keep unresolved rules as `awaiting_confirmation`; explicitly record skipped items and reasons.

## 6. Human review gate for test points

Stop after `03-test-points.md` and request human review.

In the conversation, present each point with a human-readable TP number, evidence, rule/flow, design method, and traceability. Ask for supplementary information or new points, persist the user's decision in `03-test-points.md`, and only then hand off to historical-case association/case generation; preserve added or modified points as pending until explicitly confirmed.

- If approved, continue to historical-case association.
- If rejected or modified, revise the challenge/test points and repeat this gate.

Do not generate candidate test cases before this approval.

## 7. Associate historical test cases

After test-point approval, search and read Confluence historical manual test cases using the feature, module, business-rule, and supplied-key terms. Record in `04-historical-case-association.md`:

- reused coverage;
- added coverage;
- excluded coverage and exclusion reason;
- page title, URL or page id, update time, and match reason.

Do not use an unread search result, Jira title, code, or model memory as a historical-case reference. A knowledge-base access failure blocks candidate-case generation.

## 8. Generate and review candidate cases

Write `04-test-cases.md` only after test-point approval and historical-case association. This local artifact is a normal Markdown document with one task-level metadata header; it is governed by the generator's `case-schema.md` and must not be formatted from or blocked by the Confluence `test_case_template`. Expand the confirmed test points into the actual cases `TC01`, `TC02`, and subsequent IDs. When a case requires database records, the `ai-test-case-generator` test-data contract may be used to create and verify run-scoped records in a proven non-production test database; link the resulting `04-test-data-manifest.md` to the affected cases and do not claim data exists until verification succeeds. Each case is a candidate and must include:

- priority and linked test point;
- source and evidence;
- coverage type;
- preconditions, concrete steps, and one observable expected result per step;
- historical-defect reference when it is a regression case;
- review status and adoption status.

Write `05-case-human-review.md` and stop for a separate human decision on every case: adopted, modified, or discarded. Never mark generated cases adopted automatically.

In the conversation, show the task-level metadata once, then for each unique case number such as TC01 show its linked test point, purpose, preconditions, numbered steps with one expected result per step, and priority. Ask the user to adopt, modify, or discard every case and persist the decision in `05-case-human-review.md`.

After the user completes this case-by-case confirmation, immediately run local publication validation and automatically push the adopted or modified cases to Confluence. Do not wait for or require quality-statistics approval. Exclude discarded and still-pending cases, apply the configured `test_case_template`, publish under `test_case_publish`, and persist the result in `07-delivery.md`.

## 9. Automatically publish confirmed test cases

After case review, do not block delivery on quality statistics. First validate the confirmed cases and then automatically publish them to Confluence:

- run the configured publication validator/dry-run;
- render the published content using the configured `test_case_template`;
- publish only cases marked adopted or modified by the human reviewer;
- exclude cases marked pending or discarded;
- publish under the configured `test_case_publish` space and `menu_id`;
- record the template, destination, case numbers, timestamp, page URL/ID, and result in `07-delivery.md`.

If validation or publication fails, retain the local artifacts, record the failure, and do not report successful delivery. Quality statistics may be added later and must not prevent this publication step.

For delivery/push, use the configured `test_case_template` as the Confluence published test-case format. Read and apply its field order, section names, table columns, naming conventions, status values, and example structure only when building the published content. Do not retroactively rewrite the local `04-test-cases.md` into that template. Publish only explicitly adopted or modified cases and record the destination and result in the delivery artifact.

## Artifacts

Use UTF-8 Markdown artifacts:

```text
case/<case-name>/
  00-input.md
  01-association.md
  02-review.md
  03-test-points.md
  04-historical-case-association.md
  04-test-cases.md
  05-case-human-review.md
  06-quality-metrics.md  # 暂不生成，预留后续质量统计
  07-delivery.md
```

The workflow must remain manual and evidence-backed. Do not generate automation code, push pending or discarded cases, or silently skip a human gate. Any Confluence push must use the configured `test_case_template` format at delivery time.

## Human-facing output language

For Chinese requesters, write `02-review.md`, `03-test-points.md`, `04-test-cases.md`, and `05-case-human-review.md` entirely in Chinese for human-facing labels, statuses, and coverage names. Do not expose English field names or internal enum values in those documents. Keep machine-readable English values only in internal input or validation metadata when required.

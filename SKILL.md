---
name: ai-test-case-orchestrator
description: Generate evidence-backed manual test cases from product requirements, API/interface definitions, source code, or historical defects. Route the input to the matching mode, associate Confluence/Jira/code knowledge, run one unified product/code challenge, obtain human approval for test points and cases, and evaluate coverage. Do not generate automation code.
---

# First-use credential preflight

Before any Jira, Confluence, or GitLab evidence query, check `TASKFLOW_CONFIG_PATH` and the required credentials. If the configuration is missing, remind the user to create the local user-level `lowrisk-jira.ini` described in `README.md` and stop before querying. Never ask the user to paste tokens into chat. If the configuration exists, reuse it without asking the user to log in or re-enter credentials.

# AI Test Case Orchestrator

## Interactive human-review modules

Read [interaction-contract.md](references/interaction-contract.md) whenever a human-review page or conversational review surface is produced. All three review stages use interactive HTML: 产品/代码对抗, 测试点审评, and 测试用例评审. Implement the reviewer page with a backend template engine for server-rendered initial state, HTML/CSS for structure and presentation, and Alpine.js for local form interaction. Keep the server model and persisted Markdown artifact authoritative. Render evidence cards with document title, knowledge summary, source type, update time, source link, and a plain-language association reason; use human-readable numbers such as E01/Q01/TP01/TC01 while retaining internal IDs only in data attributes. A button click is not a submission: wire forms to the host review bridge, wait for persistence acknowledgement, and only then transition to the next stage. If the bridge is unavailable or persistence fails, keep the current stage active and show a retryable error. Do not use prose-only confirmation prompts, and do not let a submit action bypass a human gate.

Follow the flow below. Keep the stages separate and preserve traceability from input to final test cases.

## 1. Route the input

Select one or more applicable modes from the supplied evidence; do not require every input to be a Git commit.

| Input | Mode | Main focus |
|---|---|---|
| PRD, user story, Jira requirement, business rule | `requirement` | actors, rules, states, acceptance criteria |
| OpenAPI/Swagger JSON or YAML, API contract | `openapi` | paths, methods, parameters, enums, responses, security, idempotency |
| source files, repository, commit, diff | `source_code` | entry points, branches, exceptions, persistence, dependencies, transactions |
| defect record or historical-defect knowledge-base evidence | `historical_defect` | symptom, trigger, root cause, fix, regression |
| anonymized traffic or behavior aggregates | `business_profile` | frequency, unusual combinations, error distribution; supplemental only |

Record `generation_mode`, `source_type`, `source_reference`, `prompt_version`, and `rule_version` in `00-input.md`. If multiple modes apply, record all of them and keep their evidence distinct.

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

The review page must show associated business, technical, and verified-code evidence at the top as readable evidence cards. Number questions as Q01, Q02, etc.; do not expose opaque evidence IDs as question labels. Render one input box per finding/question and a `提交评审` button. The button must submit through the host bridge, persist `02-review.md`, receive an acknowledgement, and only then hand off to test-point analysis. Record each response and disposition.

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

Render each point with a human-readable TP number, its related evidence cards, rule/flow, applied design method, traceability, and an input for supplementary information. Provide `新增测试点` and `提交测试点评审` buttons. The submit action must persist `03-test-points.md`, receive an acknowledgement, and only then hand off to historical-case association/case generation; preserve added or modified points as pending until explicitly confirmed.

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

Write `04-test-cases.md` only after test-point approval and historical-case association. When a case requires database records, the `ai-test-case-generator` test-data contract may be used to create and verify run-scoped records in a proven non-production test database; link the resulting `04-test-data-manifest.md` to the affected cases and do not claim data exists until verification succeeds. Each case is a candidate and must include:

- priority and linked test point;
- source and evidence;
- coverage type;
- preconditions, concrete steps, and one observable expected result per step;
- historical-defect reference when it is a regression case;
- review status and adoption status.

Write `05-case-human-review.md` and stop for a separate human decision on every case: adopted, modified, or discarded. Never mark generated cases adopted automatically.

The interactive case-review page must show linked evidence cards, the linked task/requirement URL, requirement explanation, a human-readable unique case number such as TC01, purpose, preconditions, numbered steps, matching expected results, and priority for every case. Provide editable review inputs and a `提交测试用例评审` button. The submit action must persist `05-case-human-review.md`, receive an acknowledgement, and only then hand off to quality metrics/delivery. Follow the full HTML, bridge, evidence-card, numbering, acknowledgement, and payload requirements in `interaction-contract.md`.

## 9. Evaluate quality and coverage

After case review, calculate:

- test-point coverage, including 100% P0 coverage;
- candidate/adopted/modified/discarded counts;
- adoption rate: adopted cases divided by generated candidates;
- execution effectiveness when execution data exists: passed divided by executed.

If the overall evaluation score is greater than 60%, pass the quality gate and deliver the reviewed test cases. If it is 60% or lower, return to association/challenge or test-point analysis, strengthen missing coverage, and repeat human review. Never fabricate execution data.

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
  06-quality-metrics.md
```

The workflow must remain manual and evidence-backed. Do not generate automation code, write to a test-management platform, or silently skip a human gate.

## Human-facing output language

For Chinese requesters, write `02-review.md`, `03-test-points.md`, `04-test-cases.md`, and `05-case-human-review.md` entirely in Chinese for human-facing labels, statuses, and coverage names. Do not expose English field names or internal enum values in those documents. Keep machine-readable English values only in internal input or validation metadata when required.

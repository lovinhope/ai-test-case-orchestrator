# Human-review interaction contract

All human-review modules must be rendered as interactive HTML. Markdown is the persisted audit artifact; HTML is the reviewer-facing interaction surface. Do not replace required inputs with prose-only prompts.

## Rendering stack

Support the following implementation stack for reviewer pages:

- **Backend template engine:** Render the initial page, evidence cards, human-readable numbers, initial form state, CSRF token, run/stage metadata, and bridge configuration on the server. The engine may be Jinja2, Thymeleaf, FreeMarker, or the host application's equivalent; keep template syntax isolated from Alpine expressions.
- **HTML/CSS:** Use semantic HTML for structure and accessible labels, and plain CSS for layout, evidence-card styling, read-only/read-write distinction, validation messages, loading state, and responsive display. Do not depend on client-side rendering to make the evidence or core fields exist.
- **Alpine.js:** Use Alpine.js for local state and interaction only: `x-data`, `x-model`, `x-show`, `x-for`, `x-bind`, and `x-on:submit.prevent`. Alpine must not be the source of truth for workflow state or evidence; the server payload and persisted Markdown artifact remain authoritative.

Expose server data through one escaped JSON model, for example `data-review-model`, or a safely serialized `<script type="application/json">` block. Do not interpolate raw evidence, URLs, reviewer text, or JSON directly into JavaScript. Initialize Alpine from that model and preserve the stable internal IDs in `data-*` attributes.

The template must render a usable read-only page when Alpine.js is unavailable. Dynamic additions and submission may be disabled in that mode, but evidence, numbering, existing fields, and a clear unavailable-interaction message must remain visible. Load Alpine with the host-approved version and CSP policy; do not fetch arbitrary scripts from evidence URLs.

## Submission and stage-transition protocol

An HTML button alone is not a workflow submission. Every review page must be mounted with a host-provided bridge named `window.__TEST_REVIEW_BRIDGE__` (or an equivalent explicitly documented adapter). The page must:

1. Build a complete structured payload from the current form, including `run_id`, `stage`, `artifact_path`, `item_id`/`case_id`, all reviewer inputs, and the explicit decision.
2. Validate required fields and unresolved items before calling the bridge.
3. Call `await window.__TEST_REVIEW_BRIDGE__.submit(payload)` from the form submit handler; do not use a no-op click handler or only update the DOM.
4. Wait for an acknowledgement containing `accepted`, `persisted_artifact`, and `next_stage` (or an error). Disable the submit button while the request is pending and prevent duplicate submissions.
5. On success, persist the returned review payload and decision to the current Markdown artifact, then invoke the host transition callback or return the `next_stage` token to the workflow runner. The next stage must not start before persistence succeeds.
6. On failure, keep the page and reviewer inputs intact, show the backend error, and leave the stage unchanged. Never display “提交成功” based only on client-side state.

The host bridge contract is:

```js
const result = await window.__TEST_REVIEW_BRIDGE__.submit({
  run_id, stage, artifact_path, items, reviewer, submitted_at
});
// result: { accepted: true, persisted_artifact: "...", next_stage: "..." }
```

If the bridge is unavailable, render a blocking “无法提交到下一流程” state and expose the serialized payload for the host/user to retry; do not silently fall back to a local-only submission or advance the workflow.

## Evidence cards and human-readable numbering

- Render each associated evidence item as a visible evidence card before the related question, test point, or case. The card must show: `证据编号`, document title, knowledge summary, source type, updated time when available, and a clickable source URL/page link.
- The document title and summary are mandatory display fields. Never show only a page ID, database ID, commit SHA, file path, or internal evidence key as the visible label.
- Use short human-readable labels such as `证据 E01`, `问题 Q01`, `测试点 TP01`, and `测试用例 TC01`. Keep the internal stable identifier in `data-evidence-id`, `data-question-id`, `data-test-point-id`, or `data-case-id` for persistence and tracing.
- Display the association reason in plain Chinese, for example “支持产品权限规则” or “证明接口分支与异常处理”，and provide an expandable “查看证据摘要” region when the summary is longer than two lines.
- Keep source links safe and escaped. A missing title or summary is a data-quality error: mark the item as `证据待补充` and do not silently substitute an opaque identifier.

## 1. Product/code challenge

- Render the associated business, technical, and verified-code evidence at the top of the page, before findings.
- Render one finding per question. Each question must have exactly one dedicated text input or textarea for reviewer feedback.
- Preserve the finding's evidence, source reference, rationale, and disposition next to its input.
- Provide a `提交评审` button. Submission records the reviewer response and decision; it must not silently approve unresolved findings or bypass the human gate.

## 2. Test-point review

- Render every test point with its rule, business flow, and applied test-design method (for example boundary-value, equivalence-class, decision-table, state-transition, scenario, or risk-based analysis).
- Provide one input for supplementary information or correction for each point.
- Provide an `新增测试点` button that adds a complete editable test-point row, including title, rule/flow, design method, expected observable result, priority, and traceability/source.
- Provide a `提交测试点评审` button. New and modified points remain pending human review until explicitly confirmed.

## 3. Test-case review

- Every case must show a linked task or requirement URL, requirement explanation, unique case number, purpose, preconditions, numbered test steps, matching expected results, and priority.
- Keep one expected result for each numbered step; do not collapse expected results into an uncheckable paragraph.
- Provide editable reviewer inputs for changes and a `提交测试用例评审` button.
- Submission records an explicit per-case decision: adopted, modified, or discarded. Generated cases remain candidates until the reviewer submits a decision.

## HTML implementation rules

- Use semantic HTML: `section`, `form`, `fieldset`, `legend`, `label`, `input`, `textarea`, `button`, and tables where appropriate.
- Give every input a stable unique `id` and matching `for`; include machine-readable identifiers in `data-*` attributes.
- Show human-readable numbers in headings and labels while retaining stable internal IDs in `data-*` attributes; do not expose opaque IDs as the primary numbering.
- Use `type="url"` for task/requirement links, `type="number"` or a constrained select for priority, and ordered lists for numbered steps.
- Add client-side required-field validation, but never treat client-side validation as evidence or as approval.
- Keep evidence read-only and visually distinguish it from editable reviewer fields.
- Submit a structured payload containing the run id, stage, item id, reviewer inputs, and decision. Persist the same payload in the Markdown artifact.
- Wire the form's `submit` event to the host bridge and handle acknowledgement, persistence, transition, loading, duplicate-submit, and failure states as specified above.
- Do not execute arbitrary page scripts from evidence content. Escape evidence before inserting it into HTML.
- Keep backend template expressions and Alpine expressions distinguishable; do not let the template engine evaluate Alpine expressions or let user/evidence text become template code.
- Bind the form to Alpine with `x-data` and `x-on:submit.prevent`, but delegate actual persistence and stage transition to the host bridge protocol above.
- Use CSS classes and `aria-live`/`aria-busy` for validation, submitting, success, and failure states; never rely on color alone.

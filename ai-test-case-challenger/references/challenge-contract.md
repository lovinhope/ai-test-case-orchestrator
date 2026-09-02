# Challenge contract

Review three distinct surfaces:

1. Product: missing actors, states, permissions, boundaries, defaults, exceptions, and acceptance rules.
2. Code/interface: changed branches, API/schema, persistence, transaction, idempotency, authorization, compatibility, and error handling.
3. Integration: mismatch between business evidence, caller contract, and the verified diff.

For every finding, render exactly these human-facing Markdown fields in this exact order: `来源类型`、`来源及依据`、`证据`、`风险`、`处置`、`理由`、`请确认`. Do not use English machine keys as visible replacements. Also retain machine-readable `finding_id`, optional `commit_id`, `source_reference`, and `disposition` in internal metadata (front matter or HTML comments). “来源及依据” must identify the retained evidence; “风险” must state the product/code risk; “处置” may only be `awaiting_confirmation` or `skipped`; “理由” must explain the disposition; and “请确认” must contain the concrete question or observable behavior. Mark missing evidence `awaiting_confirmation` and still render all seven fields.

State preservation: confirmed or discarded findings are terminal historical records. Regeneration uses a new revision/generation ID and new finding IDs for changed findings; it never edits the prior finding, its disposition, or its review decision.

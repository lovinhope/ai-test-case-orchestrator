---
name: ai-test-case-challenger
description: Challenge one product requirement and its optional implementation evidence. Use after ai-test-case-associator and before test-point generation; never mix multiple commits.
---

# Commit challenge

Read the local [challenge-contract.md](references/challenge-contract.md), the matching association artifact, the parent evidence references, and optional verified code evidence. Run `scripts/challenge_commit.py` to validate the optional upstream `commit_id` when one is supplied. Write `02-review.md` with independent product, code/interface, and integration/contract sections. Every finding must render exactly these human-facing fields in this exact order: `来源类型`、`来源及依据`、`证据`、`风险`、`处置`、`理由`、`请确认`. The labels and order are mandatory: never replace them with English keys, merge them, or omit them. Each field is mandatory, including when its value is “待补充” or “不适用”. Machine fields such as `finding_id`, `commit_id`, `source_reference`, and `disposition` may only appear in metadata or HTML comments and cannot replace the seven visible fields. This stage only challenges potential risks and incomplete/conflicting rules; findings may use only `awaiting_confirmation` or `skipped`. It does not generate test points or regression points. Record the human review decision and any responses in the Markdown artifact before continuing. Do not convert an inferred behavior into a fact.

When a finding is modified, delete the old revision and create a new `generation_id`/revision under `revisions/<revision>/02-review.md`, with new finding IDs and a supersession reference. A finding marked `skipped` is not regenerated unless explicitly modified. Do not retain the old revision as an active artifact.

Keep this stage independent: it challenges one requirement and optional implementation evidence; it does not generate test points or cases. Store the artifact in this sub-skill's own case directory.

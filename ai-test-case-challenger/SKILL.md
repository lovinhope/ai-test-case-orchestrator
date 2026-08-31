---
name: ai-test-case-challenger
description: Challenge the product rules and implementation contract of one verified Git commit. Use after ai-test-case-associator and before test-point generation; never mix multiple commits.
---

# Commit challenge

Read the local [challenge-contract.md](references/challenge-contract.md), the matching association artifact, the parent evidence references, and the verified diff. Run `scripts/challenge_commit.py` to enforce that the upstream `commit_id` matches. Write `02-review.md` with independent product, code/interface, and integration/contract sections. Every finding must render these human-facing fields in this exact order: `来源类型`、`来源及依据`、`证据`、`风险`、`处置`、`理由`、`请确认`. Each field is mandatory, including when its value is “待补充” or “不适用”. Each finding must cite the commit or retained evidence and use `test_point`, `regression`, `awaiting_confirmation`, or `skipped` disposition. Record the human review decision and any responses in the Markdown artifact before continuing. Do not convert an inferred behavior into a fact.

The challenge artifact is append-only by revision. Once a finding is human-confirmed or marked `skipped`/`废弃`, its finding ID, disposition, decision, and evidence are immutable. A regenerated challenge must use a new `generation_id`/revision and be written under `revisions/<revision>/02-review.md`; it may reference the prior artifact but must not overwrite it or change its original state graph. Only newly identified or explicitly superseding findings may receive new IDs.

Keep this stage independent: it challenges the one commit and does not generate test points or cases. Store the artifact in this sub-skill's own case directory.

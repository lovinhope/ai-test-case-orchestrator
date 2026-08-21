---
name: ai-test-case-challenger
description: Challenge the product rules and implementation contract of one verified Git commit. Use after ai-test-case-associator and before test-point generation; never mix multiple commits.
---

# Commit challenge

Read the local [challenge-contract.md](references/challenge-contract.md), the parent [interaction-contract.md](../references/interaction-contract.md), the matching association artifact, the parent evidence references, and the verified diff. Run `scripts/challenge_commit.py` to enforce that the upstream `commit_id` matches. Write `02-review.md` with independent product, code/interface, and integration/contract sections. Each finding must cite the commit or retained evidence and use `test_point`, `regression`, `awaiting_confirmation`, or `skipped` disposition. The reviewer-facing module must show associated evidence at the top, provide one input per finding/question, and include a submit-review action. Do not convert an inferred behavior into a fact.

Keep this stage independent: it challenges the one commit and does not generate test points or cases. Store the artifact in this sub-skill's own case directory.

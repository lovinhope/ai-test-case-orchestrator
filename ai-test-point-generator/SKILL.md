---
name: ai-test-point-generator
description: Generate traceable manual test points from one commit's association and challenge artifacts. Use after challenge review; pause for human confirmation before case generation.
---

# Commit test points

Read [test-point-rules.md](references/test-point-rules.md), the parent [interaction-contract.md](../references/interaction-contract.md), including the systematic coverage method, the matching `01-association.md`, and `02-review.md`. Run `scripts/generate_test_points.py` to verify the same `commit_id` and scaffold `03-test-points.md`. Decompose the confirmed requirements and evidence into traceable rules, apply the scenario-dimension checklist and appropriate test-design models, record requirement-to-point traceability, prioritize depth by risk, and perform the reverse coverage review before presenting points. Convert verified findings and commit behavior into business-outcome test points; include happy path, negative, boundary, exception, permission, consistency, compatibility, and historical regression where applicable. The reviewer-facing page must show each point's rule/flow/design method, provide a supplementary input, and support adding a complete test point and submitting the review. Keep unresolved items as `awaiting_confirmation` or `skipped` with reasons.

Set `status: pending_confirmation` and stop. Never generate `04-test-cases.md` in this stage. Human changes must be recorded without changing the commit identity.

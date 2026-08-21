# Review contract

Write `02-review.md` with these independent sections:

1. **Association analysis**: related historical requirements, rules, similar features, and defects with evidence.
2. **Product challenge**: missing or conflicting rules, states, boundaries, permissions, and exception expectations.
3. **Code/interface challenge**: observed contract, branch, dependency, data, transaction, idempotency, authorization, compatibility, and error-handling risk.

For each finding use:

```markdown
### <P|C|I>-<NN> Title
- source_type: requirement | openapi | source_code | historical_defect | business_profile
- source_reference: path, endpoint, commit, or external evidence
- evidence: verified fact or `awaiting_confirmation`
- disposition: test_point | regression | awaiting_confirmation | skipped
- rationale: concise reason
```

`P` is product, `C` is code/interface, and `I` is integration/contract conflict. Do not state code exists, behavior occurs, or a defect is fixed without evidence.

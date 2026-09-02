# Review contract

Write `02-review.md` with these independent sections:

1. **Association analysis**: related historical requirements, rules, similar features, and defects with evidence.
2. **Product challenge**: missing or conflicting rules, states, boundaries, permissions, and exception expectations.
3. **Code/interface challenge**: observed contract, branch, dependency, data, transaction, idempotency, authorization, compatibility, and error-handling risk.

For each finding use the following fixed human-facing Markdown shape. The seven Chinese labels and their order are mandatory:

```markdown
### <P|C|I>-<NN> Title
- 来源类型：需求 / 接口 / 源代码 / 历史缺陷 / 业务规则
- 来源及依据：path、endpoint、commit 或外部证据
- 证据：verified fact；缺失时写“待补充”
- 风险：对产品、代码或集成的影响
- 处置：测试点 / 回归 / 待确认 / 跳过
- 理由：concise reason
- 请确认：concrete question or observable behavior
```

The English keys are machine metadata only and must not replace these visible labels.

`P` is product, `C` is code/interface, and `I` is integration/contract conflict. Do not state code exists, behavior occurs, or a defect is fixed without evidence.

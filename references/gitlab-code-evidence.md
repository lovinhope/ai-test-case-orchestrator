# GitLab code evidence

Use this reference only when Jira evidence contains a GitLab commit URL, merge-request URL, repository URL, or a verified commit SHA. Use the local, secret-bearing GitLab configuration; never copy its token into artifacts, prompts, logs, or final output.

## Read-only evidence flow

1. Read Jira comments, remote links, development metadata, and linked issues. Extract only explicit GitLab repository, merge-request, and commit references.
2. Resolve each reference against GitLab with read-only API access or an already available local clone. Prefer the commit URL or project path found in Jira over keyword search.
3. Read commit metadata and diff; for merge requests, read its metadata, changes, and associated commits. Capture repository path, MR IID or SHA, URL, author, timestamp, changed files, and a compact diff summary.
4. Use code evidence only for the code/interface review. Mark a behavior as verified only when the relevant file and diff were read. Otherwise describe it as a Jira reference or an `awaiting_confirmation` question.
5. Record the result in `01-association.md` under `gitlab_code_evidence`; cite the selected SHA or MR in `02-review.md` and resulting test points/cases.

## Mainline classification and hard gates

Classify every Jira-to-GitLab reference as `mainline_implementation`, `related_implementation`, or `regression_or_noise`. Never present `related_implementation` or `regression_or_noise` in a mainline branch/commit list.

### `mainline_implementation`

Require every condition below:

1. **Task intent**: the Jira item is a requirement, main task, or explicit parent implementation item. Its title and read description must describe the target business capability; exclude primarily auxiliary wording such as log, snapshot, monitoring, trace, configuration-only, compatibility-only, optimization, repair, check, defect, or regression.
2. **Delivery intent**: the MR title or source branch explicitly identifies the same Jira key and the same target capability. A branch containing multiple Jira keys is `awaiting_confirmation`, not mainline, until its diff can be separated by task.
3. **Core diff**: the read diff changes a domain core file, API contract, or data-processing node that directly implements the target capability. For penetration, require at least one verified hit in the supplied business rule, a penetration calculation/rate/relationship node, clause data processing, fund-layer mapping, or a named product/position penetration contract.
4. **Evidence agreement**: Jira task intent, MR/source-branch intent, and core diff must agree. A Jira key match alone never satisfies this condition.

Record a pass/fail result and factual evidence for each gate. Do not infer implementation scope from branch naming alone.

### Penetration-topic association

When the requested topic is penetration, retain a Jira task as penetration-related when it passes `penetration_context_match`. A linked GitLab diff is not a prerequisite for topic association.

- `penetration_context_match`: Jira context score is at least `0.35` and includes at least one non-title signal. Default weights are title keyword `0.10`, read body/acceptance criteria/human-authored business comment `0.45`, labels/components/Epic metadata `0.25`, and verified Jira/Confluence links `0.20`.
- `title_keyword_match`: the Jira title contains the caller's penetration keyword (for example `穿透`, `持仓穿透`, `产品穿透`, `资产穿透`) or a caller-supplied equivalent. It contributes at most `0.10` to recall and cannot independently satisfy `penetration_context_match`.

Classify a record with title-only evidence as `regression_or_noise` for a penetration search, even when it has an explicit Jira/MR link. A title may be absent when the body, labels/components/Epic, or verified linked requirement reaches the context threshold. If GitLab evidence is available, use its diff only for the separate `mainline_implementation` / `related_implementation` / `regression_or_noise` code classification; do not use an absent or non-core diff to reject a Jira task that already passed topic association. A mixed-Jira branch, or a task primarily about logging, snapshotting, interface migration, configuration, optimization, repair, validation, defect, or regression is never `mainline_implementation`.

### `related_implementation`

Use when the evidence is relevant but misses one or more mainline gates: observability/logging/snapshots, interface migration, UI/configuration, compatibility, optimization, a bug fix, a validation patch, or a mixed-Jira branch. State the missing gate(s).

### `regression_or_noise`

Use when only the Jira key, a generic keyword, a common target branch (`test`, `sep`, `deploy`), or an unrelated diff matches. Exclude it from code-review evidence and report the exclusion reason.

### Required output order

Output evidence in this order: `mainline_implementation`, `related_implementation`, then `regression_or_noise`. For each record include the Jira key, issue type, title, MR/source branch, merge commit, changed core files, classification, and failed-gate reasons where applicable.

## Boundaries

- Require only read access. Do not create comments, branches, merge requests, issues, tags, or repository changes.
- Treat a GitLab authentication, authorization, or API failure as `code_evidence_unavailable`; continue the requirement/product review using verified Jira and Confluence evidence.
- Do not infer that every commit referenced in a Jira comment implements the requested requirement. State the explicit Jira relation and compare the diff to the requirement/rule before assigning relevance.
- Do not treat a Jira-key match, a branch name, a generic `穿透` keyword, or a shared release branch as mainline evidence without passing every hard gate above.
- For a penetration-topic search, require `penetration_context_match`; do not use title-only recall, generic position/product/calculation keywords, or a Jira/MR link as a substitute for contextual business evidence. Use any available GitLab diff only to classify implementation evidence after the Jira task is retained.
- Do not use repository-wide search as a replacement for a missing Jira-to-Git reference. A user may separately supply a repository, commit, or source path as `source_code` input.

## Artifact shape

```markdown
### gitlab_code_evidence
- status: verified | no_reference | code_evidence_unavailable
- jira_reference: RISK-123 + URL
- repository: group/project
- merge_request: !42 + URL  # optional
- commit: abc1234 + URL     # one item per verified commit
- changed_files:
  - path/to/file
- diff_summary: verified factual summary
- match_reason: explicit Jira GitLab reference + diff comparison
```

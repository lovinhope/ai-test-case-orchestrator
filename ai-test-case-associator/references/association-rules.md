# Association rules

- Scope every query to the single requirement/Jira item. If a Git Commit is supplied, keep all code evidence scoped to that one supplementary commit.
- Use Confluence page bodies and read Jira fields; title keywords are recall hints only.
- Verify the supplied diff or linked GitLab commit before making implementation claims; if no commit is supplied, do not make implementation claims.
- Record repository/SHA/changed files when a commit is supplied, plus query scope, evidence URL/page id, update time, and match reason.
- Default Jira scope is `project = RISK`; record any explicit expansion.
- A successful zero-result query is valid evidence; connection, authentication, or authorization failure is a blocking shortfall.
- Never merge evidence from another commit into this case.
- Confluence retrieval must be fully paginated: follow every `next` link or cursor/start page until the reported total is consumed; record query/page/result counts and do not stop at the first page.
- Use a keyword matrix rather than only the current Jira key: current Jira/title terms, explicitly linked or historical Jira keys, business-object/rule terms, module/class/configuration/interface identifiers, and page-title variants/synonyms. Run each applicable query separately, deduplicate by page ID, and read plausible bodies before classifying.
- A historical page with a different Jira key can be direct or related evidence when its body matches the business object, rule, module, or changed flow. Exclude weekly/status-tracking pages only with an explicit read-based exclusion reason.

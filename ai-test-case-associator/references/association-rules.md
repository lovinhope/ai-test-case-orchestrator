# Association rules

- Scope every query to the single commit and its explicitly linked requirement/Jira item.
- Use Confluence page bodies and read Jira fields; title keywords are recall hints only.
- Verify the supplied diff or linked GitLab commit before making implementation claims.
- Record repository, SHA, changed files, query scope, evidence URL/page id, update time, and match reason.
- Default Jira scope is `project = RISK`; record any explicit expansion.
- A successful zero-result query is valid evidence; connection, authentication, or authorization failure is a blocking shortfall.
- Never merge evidence from another commit into this case.

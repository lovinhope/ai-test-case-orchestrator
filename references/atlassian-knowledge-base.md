# Jira/Confluence evidence via local script

Jira and Confluence evidence must be retrieved through `scripts/jira_confluence_use.py`. This reference retains the historical filename for compatibility; it no longer describes an MCP connection.

## Required commands

| Operation | Command |
|---|---|
| Jira issue read | `jira-read --issue RISK-123` |
| Jira issue search | `jira-query --projects RISK --types 任务,需求,缺陷 --json` |
| Confluence search | `confluence-search --term "业务关键词" --space SPACE --json` |
| Confluence page read | `confluence-read --page <pageId-or-URL> --max-chars 10000` |

Run the script from the Skill directory or pass its absolute path. Install `requests` from `requirements.txt` before use. Record the exact command with credentials redacted, query scope, timestamp, exit status, and result status in `01-association.md`.

## Query order

1. Search Confluence business knowledge with module, feature, rule, endpoint, and supplied Jira-key terms.
2. Read candidate pages with `confluence-read`; a search hit without a page-body read is not evidence.
3. Search and read historical-defect pages with the same terms.
4. Read supplied Jira issues with `jira-read`, and use `jira-query` for linked or scope-based issue discovery.
5. Resolve any explicit GitLab references from the read Jira evidence according to `gitlab-code-evidence.md`.

Default Jira scope is `project = RISK`. Expand beyond RISK only when the caller explicitly requests cross-project search, supplies a non-RISK issue key/URL, or names another project. Record the reason for expansion.

## Evidence qualification and ranking

Read the candidate body or Jira fields first, then calculate `relevance_score` from observable signals:

- title keyword: maximum `0.10`, candidate recall only;
- body business semantics: maximum `0.45`;
- labels, components, Epic or issue metadata: maximum `0.25`;
- explicit Jira/Confluence relationship: maximum `0.20`.

Retain topical evidence only when `relevance_score >= 0.35` and at least one non-title signal exists. Sort retained pages and issues by `updated_time DESC`, then relevance and direct-link strength. A directly linked item below the threshold may be retained as `linked_context` only after its body is read.

## Failure handling

- `no_match`: the script completed successfully with zero results; the workflow may continue.
- `blocked`: script missing, `requests` missing, configuration missing, authentication failure, authorization failure, or API failure; stop the evidence phase.

Never expose Jira/Confluence credentials or unnecessary private page content in case artifacts.

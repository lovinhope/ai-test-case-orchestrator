---
name: ai-test-case-associator
description: Associate one product requirement with business rules, related requirements, historical defects, and optional implementation evidence. A Git Commit is supplementary and is never required; never combine multiple commits.
---

# Commit association

Accept exactly one product requirement supplied as a Jira link or requirement document. Accept at most one optional `commit_id` plus readable metadata/diff as supplementary implementation evidence. Read [association-rules.md](references/association-rules.md) and the parent skill's Atlassian/GitLab evidence references before querying. Search and read Confluence business and defect evidence, Jira links, and optional code evidence; search results alone are not evidence.

## Retrieval completeness requirements

For every configured Confluence search, exhaust pagination before concluding that a page is not found. Follow the connector/API `next` link or advance the `start`/cursor until the returned page is empty or the reported total is fully consumed. Record the number of pages and results traversed; never treat the first 20 results as the complete result set.

Build a keyword matrix from the Jira item, commit metadata/diff, and already-read evidence. Run separate searches for each applicable category and deduplicate by page ID:

- current Jira key and title terms;
- explicitly linked Jira keys and historical Jira keys found in related pages, comments, deployment notes, or commit messages;
- business objects and rules;
- implementation/module identifiers, configuration keys, table names, and endpoint names;
- page-title variants and synonyms.

Read the full body of every plausible hit, inspect ancestors/parent indexes and linked child pages where available, then classify it as `direct`, `related`, `legacy_reference`, `compatibility_reference`, `excluded`, or `noise`. Exclude weekly reports, QA plans, release notes, daily summaries, and other status-tracking pages only after reading enough metadata/body to establish that classification. A page with a historical Jira key must not be excluded merely because its key differs from the current Jira key.

Before returning `no_match`, report the keyword categories searched, pagination totals, deduplication count, read failures, and exclusion reasons. A connector failure remains a blocking shortfall; a completed multi-query, fully paginated search with no retained evidence is valid `no_match`.

Create `case/<case-name>/00-input.md` without changing the commit identity, then run `scripts/associate_commit.py` to validate the boundary and scaffold the artifact. Write `01-association.md` with query scope, timestamps, retained evidence, match reasons, and explicit unavailable/zero-result states. Separate business evidence from code evidence and classify every linked implementation as mainline, related, or noise. Return only evidence-backed associations to the parent.

The output is stage-local and must contain the requirement reference and `status: complete|blocked|awaiting_confirmation`. When supplied, retain `commit_id` and `commit_reference` as supplementary evidence. A branch name, MR title, or Jira title cannot substitute for a supplied commit, but a commit is optional.

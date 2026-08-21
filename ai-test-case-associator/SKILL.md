---
name: ai-test-case-associator
description: Associate one verified Git commit with business rules, related requirements, historical defects, and implementation evidence. Use as the association stage of ai-test-case-orchestrator; never combine multiple commits.
---

# Commit association

Accept only one `commit_id` plus its readable metadata/diff. Read [association-rules.md](references/association-rules.md) and the parent skill's Atlassian/GitLab evidence references before querying. Search and read Confluence business and defect evidence, Jira links, and the commit diff; search results alone are not evidence.

Create `case/<case-name>/00-input.md` without changing the commit identity, then run `scripts/associate_commit.py` to validate the boundary and scaffold the artifact. Write `01-association.md` with query scope, timestamps, retained evidence, match reasons, and explicit unavailable/zero-result states. Separate business evidence from code evidence and classify every linked implementation as mainline, related, or noise. Return only evidence-backed associations to the parent.

The output is stage-local and must contain `commit_id`, `commit_reference`, and `status: complete|blocked|awaiting_confirmation`. A branch name, MR title, or Jira title cannot substitute for a commit.

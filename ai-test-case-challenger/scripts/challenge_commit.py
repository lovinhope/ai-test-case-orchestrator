#!/usr/bin/env python3
"""Enforce commit identity before creating a challenge scaffold."""
import argparse
from pathlib import Path
def main():
    p = argparse.ArgumentParser(); p.add_argument("--case-dir", required=True); p.add_argument("--commit-id", required=True); p.add_argument("--association", required=True); p.add_argument("--revision", help="new revision name for regeneration"); a = p.parse_args()
    assoc = Path(a.association).read_text(encoding="utf-8")
    if f"commit_id: {a.commit_id}" not in assoc: p.error("association artifact belongs to another commit")
    root = Path(a.case_dir); root.mkdir(parents=True, exist_ok=True)
    target = root / "revisions" / a.revision if a.revision else root
    review = target / "02-review.md"
    if (root / "02-review.md").exists() and not a.revision: p.error("02-review.md already exists; use --revision to preserve the original")
    if review.exists(): p.error(f"revision already exists: {review}")
    target.mkdir(parents=True, exist_ok=True)
    (target / "00-input.md").write_text(f"# Commit input\n\n- commit_id: {a.commit_id}\n- upstream: {a.association}\n- revision: {a.revision or 'v1'}\n", encoding="utf-8")
    review.write_text(f"# Challenge review\n\n- commit_id: {a.commit_id}\n- generation_id: {a.revision or 'v1'}\n- status: awaiting_review\n\n## Product challenge\n\n## Code/interface challenge\n\n## Integration challenge\n", encoding="utf-8")
    print(f"created challenge scaffold: {target}")
if __name__ == "__main__": main()

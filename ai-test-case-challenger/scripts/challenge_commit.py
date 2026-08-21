#!/usr/bin/env python3
"""Enforce commit identity before creating a challenge scaffold."""
import argparse
from pathlib import Path
def main():
    p = argparse.ArgumentParser(); p.add_argument("--case-dir", required=True); p.add_argument("--commit-id", required=True); p.add_argument("--association", required=True); a = p.parse_args()
    assoc = Path(a.association).read_text(encoding="utf-8")
    if f"commit_id: {a.commit_id}" not in assoc: p.error("association artifact belongs to another commit")
    root = Path(a.case_dir); root.mkdir(parents=True, exist_ok=True)
    (root / "00-input.md").write_text(f"# Commit input\n\n- commit_id: {a.commit_id}\n- upstream: {a.association}\n", encoding="utf-8")
    (root / "02-review.md").write_text(f"# Challenge review\n\n- commit_id: {a.commit_id}\n- status: awaiting_review\n\n## Product challenge\n\n## Code/interface challenge\n\n## Integration challenge\n", encoding="utf-8")
    print(f"created challenge scaffold: {root}")
if __name__ == "__main__": main()

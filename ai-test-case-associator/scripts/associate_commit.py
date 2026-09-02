#!/usr/bin/env python3
"""Create the association scaffold; an optional commit is supplementary evidence."""
import argparse
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-dir", required=True); p.add_argument("--commit-id"); p.add_argument("--commit-reference", default="")
    a = p.parse_args()
    if a.commit_id and (len(a.commit_id) < 7 or any(x in a.commit_id.lower() for x in ("..", ",", " "))): p.error("commit-id must identify exactly one commit")
    root = Path(a.case_dir); root.mkdir(parents=True, exist_ok=True)
    (root / "00-input.md").write_text(f"# Requirement input\n\n- requirement: <Jira link or requirement document>\n- commit_id: {a.commit_id or '不适用（未提供补充 Commit）'}\n- commit_reference: {a.commit_reference or '不适用'}\n- status: awaiting_evidence\n", encoding="utf-8")
    (root / "01-association.md").write_text(f"# Association\n\n- commit_id: {a.commit_id}\n- status: awaiting_evidence\n\n## Business evidence\n\n## Code evidence\n", encoding="utf-8")
    print(f"created association scaffold: {root}")
if __name__ == "__main__": main()

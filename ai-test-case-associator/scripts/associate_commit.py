#!/usr/bin/env python3
"""Validate one-commit scope and create the association artifact scaffold."""
import argparse
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-dir", required=True); p.add_argument("--commit-id", required=True); p.add_argument("--commit-reference", required=True)
    a = p.parse_args()
    if len(a.commit_id) < 7 or any(x in a.commit_id.lower() for x in ("..", ",", " ")): p.error("commit-id must identify exactly one commit")
    root = Path(a.case_dir); root.mkdir(parents=True, exist_ok=True)
    (root / "00-input.md").write_text(f"# Commit input\n\n- commit_id: {a.commit_id}\n- commit_reference: {a.commit_reference}\n- status: immutable\n", encoding="utf-8")
    (root / "01-association.md").write_text(f"# Association\n\n- commit_id: {a.commit_id}\n- status: awaiting_evidence\n\n## Business evidence\n\n## Code evidence\n", encoding="utf-8")
    print(f"created association scaffold: {root}")
if __name__ == "__main__": main()

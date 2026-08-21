#!/usr/bin/env python3
"""Verify one-commit inputs and the human gate before case scaffolding."""
import argparse
import re
from pathlib import Path
def main():
    p = argparse.ArgumentParser(); p.add_argument("--case-dir", required=True); p.add_argument("--commit-id", required=True); p.add_argument("--test-points", required=True); a = p.parse_args()
    points = Path(a.test_points).read_text(encoding="utf-8")
    if f"commit_id: {a.commit_id}" not in points: p.error("test points belong to another commit")
    if re.search(r"(?im)^- status: pending_confirmation\s*$", points): p.error("human confirmation is required before case generation")
    root = Path(a.case_dir); root.mkdir(parents=True, exist_ok=True)
    (root / "00-input.md").write_text(f"# Commit input\n\n- commit_id: {a.commit_id}\n- test_points: {a.test_points}\n", encoding="utf-8")
    (root / "04-historical-case-association.md").write_text(f"# Historical case association\n\n- commit_id: {a.commit_id}\n- status: awaiting_evidence\n", encoding="utf-8")
    (root / "04-test-cases.md").write_text(f"# Candidate manual test cases\n\n- commit_id: {a.commit_id}\n- status: pending_human_review\n", encoding="utf-8")
    print(f"created case scaffold: {root}")
if __name__ == "__main__": main()

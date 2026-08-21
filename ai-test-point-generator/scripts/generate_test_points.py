#!/usr/bin/env python3
"""Verify stage identity and create a human-gated test-point scaffold."""
import argparse
from pathlib import Path
def main():
    p = argparse.ArgumentParser(); p.add_argument("--case-dir", required=True); p.add_argument("--commit-id", required=True); p.add_argument("--association", required=True); p.add_argument("--review", required=True); a = p.parse_args()
    text = Path(a.association).read_text(encoding="utf-8") + Path(a.review).read_text(encoding="utf-8")
    if text.count(f"commit_id: {a.commit_id}") < 2: p.error("upstream artifacts do not share this commit")
    root = Path(a.case_dir); root.mkdir(parents=True, exist_ok=True)
    (root / "00-input.md").write_text(f"# Commit input\n\n- commit_id: {a.commit_id}\n- association: {a.association}\n- review: {a.review}\n", encoding="utf-8")
    (root / "03-test-points.md").write_text(f"# Test points\n\n- commit_id: {a.commit_id}\n- status: pending_confirmation\n\n## P0\n\n## P1\n\n## P2\n\n## Awaiting confirmation or skipped\n", encoding="utf-8")
    print(f"created test-point scaffold: {root}; human confirmation required")
if __name__ == "__main__": main()

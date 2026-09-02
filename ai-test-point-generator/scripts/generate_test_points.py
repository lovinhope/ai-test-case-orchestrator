#!/usr/bin/env python3
"""Verify stage identity and create a human-gated test-point scaffold."""
import argparse
from pathlib import Path
def main():
    p = argparse.ArgumentParser(); p.add_argument("--case-dir", required=True); p.add_argument("--commit-id"); p.add_argument("--association", required=True); p.add_argument("--review", required=True); p.add_argument("--revision", help="new revision name for regeneration"); a = p.parse_args()
    text = Path(a.association).read_text(encoding="utf-8") + Path(a.review).read_text(encoding="utf-8")
    if a.commit_id and text.count(f"commit_id: {a.commit_id}") < 2: p.error("upstream artifacts do not share this commit")
    root = Path(a.case_dir); root.mkdir(parents=True, exist_ok=True)
    target = root / "revisions" / a.revision if a.revision else root
    points = target / "03-test-points.md"
    if (root / "03-test-points.md").exists() and not a.revision: p.error("03-test-points.md already exists; use --revision to preserve the original")
    if points.exists(): p.error(f"revision already exists: {points}")
    target.mkdir(parents=True, exist_ok=True)
    (target / "00-input.md").write_text(f"# Commit input\n\n- commit_id: {a.commit_id}\n- generation_id: {a.revision or 'v1'}\n- association: {a.association}\n- review: {a.review}\n", encoding="utf-8")
    points.write_text(f"# Test points\n\n- commit_id: {a.commit_id}\n- generation_id: {a.revision or 'v1'}\n- source_review_revision: {a.revision or 'v1'}\n- status: pending_confirmation\n\n## 测试点确认清单\n\n| 编号 | 测试点 | 状态 |\n|---|---|---|\n\n## P0\n\n## P1\n\n## P2\n\n## Awaiting confirmation or skipped\n", encoding="utf-8")
    print(f"created test-point scaffold: {target}; human confirmation required")
if __name__ == "__main__": main()

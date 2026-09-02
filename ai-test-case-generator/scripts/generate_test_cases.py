#!/usr/bin/env python3
"""Verify requirement/test-point inputs and the human gate before case scaffolding."""
import argparse
import re
from pathlib import Path
def main():
    p = argparse.ArgumentParser(); p.add_argument("--case-dir", required=True); p.add_argument("--commit-id"); p.add_argument("--test-points", required=True); p.add_argument("--revision", help="new revision name for regeneration"); a = p.parse_args()
    points = Path(a.test_points).read_text(encoding="utf-8")
    if a.commit_id and f"commit_id: {a.commit_id}" not in points: p.error("test points belong to another commit")
    if re.search(r"(?im)^- status: pending_confirmation\s*$", points): p.error("human confirmation is required before case generation")
    root = Path(a.case_dir); root.mkdir(parents=True, exist_ok=True)
    target = root / "revisions" / a.revision if a.revision else root
    cases = target / "04-test-cases.md"
    if (root / "04-test-cases.md").exists() and not a.revision: p.error("04-test-cases.md already exists; use --revision to preserve the original")
    if cases.exists(): p.error(f"revision already exists: {cases}")
    target.mkdir(parents=True, exist_ok=True)
    (target / "00-input.md").write_text(f"# Commit input\n\n- commit_id: {a.commit_id}\n- generation_id: {a.revision or 'v1'}\n- test_points: {a.test_points}\n", encoding="utf-8")
    (target / "04-historical-case-association.md").write_text(f"# Historical case association\n\n- commit_id: {a.commit_id}\n- generation_id: {a.revision or 'v1'}\n- status: awaiting_evidence\n", encoding="utf-8")
    cases.write_text(
        "# Candidate manual test cases\n\n"
        "## 任务信息\n"
        "- 测试用例: <待填写任务名称>\n"
        "- 相关JIRA: <待填写，若有>\n"
        "- 相关业务: <待填写>\n"
        "- 相关模块: <选填>\n"
        "- 相关表: <待填写，若适用>\n"
        "- 相关配置: <选填>\n"
        "- 相关接口: <选填>\n"
        "- 相关定时任务: <选填>\n"
        "- 相关权限控制: <选填>\n"
        f"- commit_id: {a.commit_id}\n"
        "\n<!-- 已确认测试点将在此展开为 TC01、TC02 等实际测试用例。 -->\n"
        "\n- review_status: awaiting_confirmation\n- case_status: candidate\n",
        encoding="utf-8",
    )
    print(f"created case scaffold: {target}")
if __name__ == "__main__": main()

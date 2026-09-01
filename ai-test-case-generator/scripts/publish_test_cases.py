#!/usr/bin/env python3
"""Validate manual test cases and optionally publish them under a configured Confluence page."""
import argparse
import configparser
import html
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

import requests

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_ROOT / "test-case-publish.ini"
CASE_HEADER = re.compile(r"^###\s+(TC\d+)\s+(.+)$", re.M)
FIELDS = {
    "优先级": "priority", "关联测试点": "test_point", "测试点": "test_point",
    "覆盖类型": "coverage", "来源及依据": "source", "目的": "purpose",
    "前置条件": "preconditions", "测试数据": "data", "步骤与预期": "steps",
    "目的及风险": "purpose",
    "后置处理": "post_processing", "测试结果": "test_result",
}


def config(path: Path) -> Dict[str, str]:
    if not path.exists():
        raise RuntimeError(f"publish config not found: {path}")
    p = configparser.ConfigParser(); p.read(path, encoding="utf-8")
    if not p.has_section("publish"):
        raise RuntimeError("publish config must contain [publish]")
    return {k: v.strip() for k, v in p.items("publish")}


def cases(path: Path) -> List[Tuple[str, str, str]]:
    text = path.read_text(encoding="utf-8")
    found = list(CASE_HEADER.finditer(text))
    return [(m.group(1), m.group(2).strip(), text[m.end():found[i + 1].start() if i + 1 < len(found) else len(text)].strip())
            for i, m in enumerate(found)]


def field(block: str, name: str) -> str:
    labels = [k for k, v in FIELDS.items() if v == name]
    for label in labels:
        # Match the field marker on one line. Returning the case block keeps
        # multiline tables/steps available for later structural validation.
        if re.search(rf"(?m)^[ \t]*-[ \t]*{re.escape(label)}[ \t]*[:：]", block):
            return block
    return ""


def validate(case_id: str, title: str, block: str) -> List[str]:
    if "废弃" in title or re.search(r"(?m)^\s*-\s*(?:用例状态|case_status)\s*[:：]\s*废弃", block):
        return []
    errors = [f"{case_id}: missing {name}" for name in
              ("priority", "test_point", "coverage", "source", "purpose", "preconditions", "steps")
              if not field(block, name)]
    if not re.search(r"(?m)^\s*-\s*(?:评审状态|review_status)\s*[:：]", block):
        errors.append(f"{case_id}: missing review status")
    if not re.search(r"(?m)^\s*-\s*(?:采用状态|用例状态|case_status)\s*[:：]", block):
        errors.append(f"{case_id}: missing case status")
    data_block = field(block, "data") or block
    if not re.search(r"来源|准备|清理|复用|测试环境", data_block + block):
        errors.append(f"{case_id}: test data must state source/preparation/cleanup or shared-data mapping")
    steps = re.findall(r"(?m)^\s*\d+\.\s+.+$", field(block, "steps"))
    expected = re.findall(r"(?m)^\s*-\s*预期[:：].+$", block)
    if not expected:
        expected = re.findall(r"—\s*预期[:：]", field(block, "steps"))
    if not steps:
        errors.append(f"{case_id}: no numbered steps")
    if len(steps) != len(expected):
        errors.append(f"{case_id}: steps ({len(steps)}) and expected results ({len(expected)}) differ")
    if re.search(r"随便输入|正常操作|系统正常|显示正确", block):
        errors.append(f"{case_id}: vague execution/expected wording")
    return errors


def storage(markdown: str) -> str:
    """Convert the generated Markdown subset to Confluence storage HTML."""
    out, table, ul = [], False, False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if table: out.append("</tbody></table>"); table = False
            if ul: out.append("</ul>"); ul = False
            continue
        if line.startswith("### "):
            out.append(f"<h3>{html.escape(line[4:])}</h3>"); continue
        if line.strip().startswith("|") and line.strip().endswith("|"):
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r"[-: ]+", x or " ") for x in cells): continue
            if not table: out.append("<table><tbody>"); table = True
            out.append("<tr>" + "".join(f"<td>{html.escape(x)}</td>" for x in cells) + "</tr>"); continue
        if re.match(r"^\s*[-*]\s+", line):
            if not ul: out.append("<ul>"); ul = True
            item = re.sub(r"^\s*[-*]\s+", "", line)
            out.append(f"<li>{html.escape(item)}</li>"); continue
        if table: out.append("</tbody></table>"); table = False
        if ul: out.append("</ul>"); ul = False
        out.append(f"<p>{html.escape(line.strip())}</p>")
    if table: out.append("</tbody></table>")
    if ul: out.append("</ul>")
    return "".join(out)


def value(block: str, label: str) -> str:
    match = re.search(rf"(?m)^\s*-\s*{re.escape(label)}\s*[:：]\s*(.*)$", block)
    return match.group(1).strip() if match else ""


def section(block: str, label: str, next_labels: List[str]) -> str:
    stop = "|".join(re.escape(x) for x in next_labels)
    match = re.search(rf"(?ms)^\s*-\s*{re.escape(label)}\s*[:：]\s*(.*?)(?=^\s*-\s*(?:{stop})\s*[:：]|\Z)", block)
    return match.group(1).strip() if match else ""


def cell_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or re.fullmatch(r"\|?[-:| ]+\|?", line):
            continue
        if line.startswith("|") and line.endswith("|"):
            line = " / ".join(x.strip() for x in line.strip("|").split("|"))
        lines.append(line)
    return "<br/>".join(html.escape(x) for x in lines)


def strict_storage(source: str, selected: List[Tuple[str, str, str]], cfg: Dict[str, str]) -> str:
    """Render the configured Confluence format with all cases in one consolidated table."""
    jira_key = cfg.get("jira_key", "<jira-key>")
    jira_url = cfg.get("jira_url", f"http://jira.lowrisk.com.cn/browse/{jira_key}")
    jira_macro = f'<a href="{html.escape(jira_url, quote=True)}">{html.escape(jira_key)}</a>'
    requirement = cfg.get("business_requirement", "").replace("\\n", "\n")
    commits = "；".join(x.strip() for x in re.findall(r"(?m)^(?:主提交|页面关联提交)：(.+)$", source))
    out = ["<h2>关联jira</h2>", f"<p>{jira_macro}</p>", "<h2>业务需求</h2>",
           f"<p>{html.escape(requirement).replace(chr(10), '<br/>')}</p>", "<h2>实现逻辑</h2>",
           f"<p>{html.escape(commits or '见各用例来源及依据')}</p>", "<h2>测试用例</h2>",
           "<table><tbody><tr>" + "".join(f"<th>{x}</th>" for x in
           ("用例编号", "测试用例", "优先级", "测试点", "覆盖类型", "前置条件", "测试数据", "测试步骤", "预期结果", "测试结果")) + "</tr>"]
    for case_id, title, block in selected:
        data = section(block, "测试数据", ["前置条件", "步骤与预期", "评审状态"]) or "由测试环境准备；本次不创建数据库数据。"
        step_text = section(block, "步骤与预期", ["评审状态", "采用状态", "后置处理", "测试结果"])
        pairs = re.findall(r"(?ms)^\s*(\d+)\.\s*(.*?)\n\s*-\s*预期[:：]\s*(.*?)(?=\n\s*\d+\.\s|\Z)", step_text)
        if not pairs:
            pairs = re.findall(r"(?m)^\s*(\d+)\.\s*(.*?)\s*[—-]\s*预期[:：]\s*(.*)$", step_text)
        steps = "<br/>".join(f"{n}. {html.escape(a.strip())}" for n, a, _ in pairs)
        expected = "<br/>".join(f"{n}. {html.escape(e.strip())}" for n, _, e in pairs)
        cells = (case_id, title, value(block, "优先级"), value(block, "关联测试点") or value(block, "测试点"),
                 value(block, "覆盖类型"), value(block, "前置条件"), cell_text(data), steps, expected, value(block, "测试结果"))
        out.append("<tr>" + "".join(f"<td>{html.escape(x) if '<br/>' not in x else x}</td>" for x in cells) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def auth() -> Tuple[str, Dict[str, str]]:
    path = os.getenv("TASKFLOW_CONFIG_PATH", "").strip()
    if not path: raise RuntimeError("TASKFLOW_CONFIG_PATH is not configured")
    p = configparser.ConfigParser(); p.read(path, encoding="utf-8")
    base = p.get("confluence", "base_url", fallback="").strip().rstrip("/")
    token = p.get("confluence", "token", fallback="").strip()
    if not base or not token: raise RuntimeError("Confluence base_url/token missing")
    return base, {"Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", required=True); ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--case", action="append", dest="only"); ap.add_argument("--update-page", help="update an existing Confluence page instead of creating a child")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(); cfg = config(Path(args.config))
    parent = re.search(r"pageId=(\d+)", cfg.get("parent_page", ""))
    parent_id = parent.group(1) if parent else cfg.get("parent_page", "")
    if not parent_id.isdigit(): raise RuntimeError("publish.parent_page must be a page ID or URL")
    selected = [x for x in cases(Path(args.cases))
                if (not args.only or x[0] in args.only)
                and "废弃" not in x[1]
                and not re.search(r"(?m)^\s*-\s*(?:用例状态|case_status)\s*[:：]\s*废弃", x[2])]
    if not selected: raise RuntimeError("no matching test cases")
    errors = [e for x in selected for e in validate(*x)]
    if errors:
        print("\n".join("ERROR: " + e for e in errors)); return 1
    title = cfg.get("page_title") or f"{cfg.get('title_prefix', '候选测试用例')} - {Path(args.cases).parent.name}"
    source = Path(args.cases).read_text(encoding="utf-8")
    body = "<p><strong>发布状态：</strong>已完成人工评审并采用；质量标准和格式标准见配置。</p>"
    body += strict_storage(source, selected, cfg)
    print(f"PASS: {len(selected)} case(s) validated"); print(f"destination_parent_page: {parent_id}"); print(f"title: {title}")
    if args.dry_run: print(f"dry_run_storage_chars: {len(body)}"); return 0
    base, headers = auth()
    if args.update_page:
        page_resp = requests.get(f"{base}/rest/api/content/{args.update_page}?expand=version,space", headers=headers, timeout=60); page_resp.raise_for_status()
        page = page_resp.json(); version = int((page.get("version") or {}).get("number", 0))
        payload = {"type": "page", "title": page.get("title", title), "version": {"number": version + 1, "message": "按测试用例格式标准更新"}, "body": {"storage": {"value": body, "representation": "storage"}}}
        resp = requests.put(f"{base}/rest/api/content/{args.update_page}", headers=headers, json=payload, timeout=60); resp.raise_for_status()
        print(f"updated_page_id: {args.update_page}"); print(f"updated_url: {base}/pages/viewpage.action?pageId={args.update_page}"); return 0
    if cfg.get("allow_duplicate", "false").lower() != "true":
        q = requests.get(f"{base}/rest/api/content/{parent_id}/child/page", params={"limit": 200}, headers=headers, timeout=60); q.raise_for_status()
        if any(x.get("title") == title for x in q.json().get("results", [])): raise RuntimeError(f"duplicate title: {title}")
    parent_resp = requests.get(f"{base}/rest/api/content/{parent_id}?expand=space", headers=headers, timeout=60); parent_resp.raise_for_status()
    space = (parent_resp.json().get("space") or {}).get("key")
    payload = {"type": "page", "title": title, "ancestors": [{"id": parent_id},], "space": {"key": space}, "body": {"storage": {"value": body, "representation": "storage"}}}
    resp = requests.post(f"{base}/rest/api/content", headers=headers, json=payload, timeout=60); resp.raise_for_status()
    data = resp.json(); print(f"created_page_id: {data.get('id')}"); print(f"created_url: {base}{(data.get('_links') or {}).get('webui', '')}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())

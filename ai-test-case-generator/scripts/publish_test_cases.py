#!/usr/bin/env python3
"""Validate manual test cases and optionally publish them under a configured Confluence page."""
import argparse
import configparser
import html
from html.parser import HTMLParser
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


class TemplateParser(HTMLParser):
    """Extract the ordered headings and table headers from Confluence storage HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: List[Tuple[int, str]] = []
        self.tables: List[List[str]] = []
        self._heading_level: Optional[int] = None
        self._heading_parts: List[str] = []
        self._table_rows: List[List[str]] = []
        self._row: Optional[List[str]] = None
        self._cell_parts: List[str] = []
        self._in_cell = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        match = re.fullmatch(r"h([1-6])", tag.lower())
        if match:
            self._heading_level = int(match.group(1)); self._heading_parts = []
        elif tag.lower() == "table":
            self._table_rows = []
        elif tag.lower() == "tr":
            self._row = []
        elif tag.lower() in {"th", "td"} and self._row is not None:
            self._in_cell = True; self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if re.fullmatch(r"h[1-6]", tag) and self._heading_level is not None:
            self.headings.append((self._heading_level, "".join(self._heading_parts).strip()))
            self._heading_level = None
        elif tag in {"th", "td"} and self._in_cell and self._row is not None:
            self._row.append("".join(self._cell_parts).strip()); self._in_cell = False
        elif tag == "tr" and self._row is not None:
            self._table_rows.append(self._row); self._row = None
        elif tag == "table":
            if self._table_rows: self.tables.append(self._table_rows)

    def handle_data(self, data: str) -> None:
        if self._heading_level is not None: self._heading_parts.append(data)
        if self._in_cell: self._cell_parts.append(data)


def template_structure(storage_html: str) -> TemplateParser:
    parser = TemplateParser(); parser.feed(storage_html); parser.close()
    if not parser.headings or not parser.tables or not parser.tables[0]:
        raise RuntimeError("configured template must contain ordered headings and at least one table")
    return parser


def template_id() -> str:
    path = os.getenv("TASKFLOW_CONFIG_PATH", "").strip()
    if not path: raise RuntimeError("TASKFLOW_CONFIG_PATH is not configured")
    parser = configparser.ConfigParser(); parser.read(path, encoding="utf-8")
    if not parser.has_section("test_case_template"):
        raise RuntimeError("TASKFLOW_CONFIG_PATH must contain [test_case_template]")
    raw = parser.get("test_case_template", "page_id", fallback="").strip()
    if not raw: raw = parser.get("test_case_template", "url", fallback="").strip()
    match = re.search(r"(?:pageId=|/)(\d+)(?:\D|$)", raw)
    value = match.group(1) if match else raw
    if not value.isdigit(): raise RuntimeError("[test_case_template] must contain a numeric page_id or URL")
    return value


def fetch_template(base: str, headers: Dict[str, str]) -> Tuple[str, TemplateParser]:
    page = template_id()
    response = requests.get(f"{base}/rest/api/content/{page}", params={"expand": "body.storage"}, headers=headers, timeout=60)
    response.raise_for_status()
    storage_html = ((response.json().get("body") or {}).get("storage") or {}).get("value", "")
    if not storage_html: raise RuntimeError(f"template page {page} has no storage body")
    return page, template_structure(storage_html)


def normalize_label(label: str) -> str:
    return re.sub(r"[\s:：/（）()]+", "", label).lower()


def task_value(heading: str, source: str, cfg: Dict[str, str], commits: str) -> str:
    normalized = normalize_label(heading)
    aliases = {
        "关联jira": cfg.get("jira_key", "<jira-key>"),
        "业务需求": cfg.get("business_requirement", ""),
        "实现逻辑": commits or "见各用例来源及依据",
    }
    if normalized in aliases: return aliases[normalized]
    for label in ("相关模块", "相关表", "相关配置", "相关接口", "相关定时任务", "相关权限控制"):
        if normalized == normalize_label(label):
            match = re.search(rf"(?m)^-\s*{re.escape(label)}\s*[:：]\s*(.+)$", source)
            return match.group(1).strip() if match else ""
    return ""


def case_value(case_id: str, title: str, block: str, header: str) -> str:
    normalized = normalize_label(header)
    if normalized == "用例编号": return case_id
    if normalized in {"测试用例", "用例"}: return title
    mapping = {"优先级": "优先级", "测试点": "关联测试点", "关联测试点": "关联测试点",
               "覆盖类型": "覆盖类型", "来源及依据": "来源及依据", "目的": "目的",
               "前置条件": "前置条件", "测试数据": "测试数据", "测试步骤": "步骤与预期",
               "步骤与预期": "步骤与预期", "测试结果": "测试结果"}
    label = mapping.get(header, mapping.get(normalized, ""))
    if normalized in {"测试步骤", "步骤与预期"}:
        text = section(block, "步骤与预期", ["评审状态", "采用状态", "用例状态", "后置处理", "测试结果"])
        pairs = re.findall(r"(?ms)^\s*(\d+)\.\s*(.*?)\n\s*-\s*预期[:：]\s*(.*?)(?=\n\s*\d+\.\s|\Z)", text)
        return "<br/>".join(f"{n}. {html.escape(a.strip())}" for n, a, _ in pairs)
    if normalized == "预期结果":
        text = section(block, "步骤与预期", ["评审状态", "采用状态", "用例状态", "后置处理", "测试结果"])
        pairs = re.findall(r"(?ms)^\s*(\d+)\.\s*(.*?)\n\s*-\s*预期[:：]\s*(.*?)(?=\n\s*\d+\.\s|\Z)", text)
        return "<br/>".join(f"{n}. {html.escape(e.strip())}" for n, _, e in pairs)
    if label == "测试结果": return value(block, "测试结果")
    if label == "测试数据": return cell_text(section(block, label, ["前置条件", "步骤与预期", "评审状态"]) or "由测试环境准备；本次不创建数据库数据。")
    if label == "前置条件": return cell_text(value(block, label))
    return value(block, label)


def render_from_template(source: str, selected: List[Tuple[str, str, str]], cfg: Dict[str, str], template: TemplateParser) -> str:
    """Render only the ordered headings and first-table schema learned from the template."""
    jira_key = cfg.get("jira_key", "<jira-key>")
    jira_url = cfg.get("jira_url", f"http://jira.lowrisk.com.cn/browse/{jira_key}")
    requirement = cfg.get("business_requirement", "").replace("\\n", "\n")
    commits = "；".join(x.strip() for x in re.findall(r"(?m)^(?:主提交|页面关联提交)：(.+)$", source))
    out: List[str] = []
    table_headers = template.tables[0][0]
    table_heading = normalize_label("测试用例")
    for level, heading in template.headings:
        tag = f"h{level}"
        out.append(f"<{tag}>{html.escape(heading)}</{tag}>")
        if normalize_label(heading) == table_heading:
            out.append("<table><tbody><tr>" + "".join(f"<th>{html.escape(x)}</th>" for x in table_headers) + "</tr>")
            for case_id, title, block in selected:
                cells = [case_value(case_id, title, block, header) for header in table_headers]
                out.append("<tr>" + "".join(f"<td>{x if '<br/>' in x else html.escape(x)}</td>" for x in cells) + "</tr>")
            out.append("</tbody></table>")
        else:
            text = task_value(heading, source, cfg, commits)
            out.append(f"<p>{html.escape(text).replace(chr(10), '<br/>')}</p>")
    return "".join(out)


def structure_signature(storage_html: str) -> Tuple[List[Tuple[int, str]], List[List[str]]]:
    parsed = template_structure(storage_html)
    return parsed.headings, [rows[0] for rows in parsed.tables]


def assert_template_structure(template: TemplateParser, rendered: str) -> None:
    headings, tables = structure_signature(rendered)
    expected = (template.headings, [rows[0] for rows in template.tables])
    if (headings, tables) != expected:
        raise RuntimeError("rendered content does not match template heading/table structure; publication blocked")


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
    base, headers = auth()
    template_page, template = fetch_template(base, headers)
    body = render_from_template(source, selected, cfg, template)
    assert_template_structure(template, body)
    print(f"PASS: {len(selected)} case(s) validated"); print(f"destination_parent_page: {parent_id}"); print(f"title: {title}")
    print(f"template_page_id: {template_page}")
    if args.dry_run: print(f"dry_run_storage_chars: {len(body)}"); return 0
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

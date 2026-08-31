#!/usr/bin/env python3
"""Validate candidate manual cases and optionally publish them as a Confluence child page."""

import argparse
import configparser
import html
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import requests


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_ROOT / "test-case-publish.ini"
CASE_HEADER = re.compile(r"^###\s+(TC\d+)\s+(.+)$", re.M)
REQUIRED_LABELS = {
    "priority": ("优先级", "priority"),
    "test_point": ("关联测试点", "测试点", "test_point"),
    "coverage": ("覆盖类型", "coverage_type"),
    "source": ("来源及依据", "source_reference"),
    "purpose": ("目的", "purpose"),
    "preconditions": ("前置条件", "preconditions"),
    "data": ("测试数据", "test_data"),
    "steps": ("步骤与预期", "测试步骤", "steps"),
}


def read_config(path: Path) -> Dict[str, str]:
    parser = configparser.ConfigParser()
    if not path.exists():
        raise RuntimeError(f"publish config not found: {path}")
    parser.read(path, encoding="utf-8")
    if not parser.has_section("publish"):
        raise RuntimeError("publish config must contain [publish]")
    return {k: v.strip() for k, v in parser.items("publish")}


def read_cases(path: Path) -> List[Tuple[str, str, str]]:
    text = path.read_text(encoding="utf-8")
    matches = list(CASE_HEADER.finditer(text))
    return [
        (m.group(1), m.group(2).strip(), text[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(text)].strip())
        for i, m in enumerate(matches)
    ]


def has_label(block: str, labels: Iterable[str]) -> bool:
    return any(re.search(rf"(?m)^\s*-\s*{re.escape(label)}\s*:", block) for label in labels)


def section_text(block: str, labels: Iterable[str]) -> str:
    for label in labels:
        match = re.search(rf"(?ms)^\s*-\s*{re.escape(label)}\s*:\s*(.*?)(?=^\s*-\s+[^-]|\Z)", block)
        if match:
            return match.group(1).strip()
    return ""


def validate_case(case_id: str, title: str, block: str) -> List[str]:
    errors: List[str] = []
    if "废弃" in title or re.search(r"(?m)^\s*-\s*(?:用例状态|case_status)\s*:\s*废弃", block):
        return [f"{case_id}: discarded case must not be published"]
    if not title or title.startswith("（"):
        errors.append(f"{case_id}: missing usable title")
    for name, labels in REQUIRED_LABELS.items():
        if not has_label(block, labels):
            errors.append(f"{case_id}: missing {name}")
    if not re.search(r"(?m)^\s*-\s*(?:评审状态|review_status)\s*:", block):
        errors.append(f"{case_id}: missing review status")
    if not re.search(r"(?m)^\s*-\s*(?:采用状态|用例状态|case_status)\s*:", block):
        errors.append(f"{case_id}: missing case status")
    steps = re.findall(r"(?m)^\s*\d+\.\s+.+$", section_text(block, REQUIRED_LABELS["steps"]))
    expected = re.findall(r"(?m)^\s*-\s*预期：.+$", block)
    if not steps:
        errors.append(f"{case_id}: no numbered steps")
    if len(steps) != len(expected):
        errors.append(f"{case_id}: numbered steps ({len(steps)}) and expected results ({len(expected)}) do not match")
    if re.search(r"随便输入|正常操作|系统正常|显示正确", block):
        errors.append(f"{case_id}: contains vague execution or expected-result wording")
    return errors


def inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def markdown_to_storage(markdown: str) -> str:
    """Small deterministic Markdown subset converter; generated case files use this subset."""
    lines = markdown.splitlines()
    out: List[str] = []
    in_table = False
    in_list = False
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            if in_list:
                out.append("</ul>"); in_list = False
            if in_table:
                out.append("</table>"); in_table = False
            continue
        if line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>"); continue
        if re.match(r"^\s*\|.*\|\s*$", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r"[-: ]+", c or " ") for c in cells):
                continue
            if not in_table:
                out.append("<table><tbody>"); in_table = True
            tag = "th" if not any("<tr>" in x for x in out[-2:]) else "td"
            out.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
            continue
        if re.match(r"^\s*[-*]\s+", line):
            if not in_list:
                out.append("<ul>"); in_list = True
            list_item = re.sub(r"^\s*[-*]\s+", "", line)
            out.append(f"<li>{inline(list_item)}</li>"); continue
        if in_list:
            out.append("</ul>"); in_list = False
        if in_table:
            out.append("</table>"); in_table = False
        if re.match(r"^\s*\d+\.\s+", line):
            out.append(f"<p>{inline(line.strip())}</p>"); continue
        out.append(f"<p>{inline(line)}</p>")
    if in_list: out.append("</ul>")
    if in_table: out.append("</table>")
    return "".join(out)


def confluence_auth() -> Tuple[str, Dict[str, str]]:
    config_path = os.getenv("TASKFLOW_CONFIG_PATH", "").strip()
    if not config_path:
        raise RuntimeError("TASKFLOW_CONFIG_PATH is not configured")
    parser = configparser.ConfigParser(); parser.read(config_path, encoding="utf-8")
    base = parser.get("confluence", "base_url", fallback="").strip().rstrip("/")
    token = parser.get("confluence", "token", fallback="").strip()
    if not base or not token:
        raise RuntimeError("Confluence base_url/token missing in TASKFLOW_CONFIG_PATH")
    return base, {"Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json"}


def page_id(value: str) -> str:
    match = re.search(r"pageId=(\d+)", value or "")
    return match.group(1) if match else (value or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True, help="path to 04-test-cases.md")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="push config; defaults to skill directory")
    parser.add_argument("--case", action="append", dest="case_ids", help="publish only this case ID; repeatable")
    parser.add_argument("--dry-run", action="store_true", help="validate and render without creating a page")
    args = parser.parse_args()

    cfg = read_config(Path(args.config))
    parent = page_id(cfg.get("parent_page", ""))
    if not parent.isdigit():
        raise RuntimeError("publish.parent_page must be a Confluence page ID or URL")
    selected = [c for c in read_cases(Path(args.cases)) if not args.case_ids or c[0] in args.case_ids]
    if not selected:
        raise RuntimeError("no matching test cases found")
    errors = [e for case in selected for e in validate_case(*case)]
    if errors:
        for error in errors: print(f"ERROR: {error}")
        return 1
    title = cfg.get("page_title") or f"{cfg.get('title_prefix', '测试用例')} - {Path(args.cases).parent.name}"
    body = "<p><strong>发布状态：</strong>候选草稿，待人工评审；来源格式标准和质量标准见配置。</p>"
    body += markdown_to_storage(Path(args.cases).read_text(encoding="utf-8"))
    print(f"PASS: {len(selected)} case(s) validated")
    print(f"destination_parent_page: {parent}")
    print(f"title: {title}")
    if args.dry_run:
        print(f"dry_run_storage_chars: {len(body)}")
        return 0
    base, headers = confluence_auth()
    duplicate = str(cfg.get("allow_duplicate", "false")).lower() == "true"
    if not duplicate:
        q = requests.get(f"{base}/rest/api/content/{parent}/child/page", params={"limit": 200, "expand": "title"}, headers=headers, timeout=60)
        q.raise_for_status()
        if any(p.get("title") == title for p in q.json().get("results", [])):
            raise RuntimeError(f"duplicate child page title: {title}")
    parent_resp = requests.get(f"{base}/rest/api/content/{parent}?expand=space", headers=headers, timeout=60)
    parent_resp.raise_for_status()
    space_key = (parent_resp.json().get("space") or {}).get("key")
    payload = {"type": "page", "title": title, "ancestors": [{"id": parent}], "space": {"key": space_key}, "body": {"storage": {"value": body, "representation": "storage"}}}
    resp = requests.post(f"{base}/rest/api/content", headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json(); link = (data.get("_links") or {}).get("webui", "")
    print(f"created_page_id: {data.get('id')}")
    print(f"created_url: {base}{link}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

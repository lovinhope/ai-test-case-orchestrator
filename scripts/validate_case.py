#!/usr/bin/env python3
"""Validate static quality gates in an orchestrator case directory."""
import argparse
import re
from pathlib import Path


CASE_RE = re.compile(r"^##\s+((?:TC[\w-]+|用例\d+))\s+(.+)$", re.M)
TP_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s+(TP[\w-]+).*$", re.M)

FIELD_ALIASES = {
    "source_type": ("source_type", "来源类型"),
    "source_reference": ("source_reference", "来源及依据"),
    "coverage_type": ("coverage_type", "覆盖类型"),
    "review_status": ("review_status", "评审状态"),
    "case_status": ("case_status", "用例状态"),
    "test_point": ("test_point", "测试点"),
    "historical_defect_reference": ("historical_defect_reference", "历史缺陷依据"),
    "steps": ("steps", "测试步骤"),
    "expected_results": ("expected_results", "预期结果"),
}


def blocks(text):
    matches = list(CASE_RE.finditer(text))
    for idx, match in enumerate(matches):
        yield match.group(1), match.group(2).strip(), text[match.end(): matches[idx + 1].start() if idx + 1 < len(matches) else len(text)]


def numbered_count(block, label):
    labels = FIELD_ALIASES.get(label, (label,))
    lines = block.splitlines()
    start = next((i + 1 for i, line in enumerate(lines) if line.strip() in {f"- {item}:" for item in labels}), None)
    if start is None:
        return 0
    values = []
    for line in lines[start:]:
        if line.startswith("- "):
            break
        values.append(line)
    return len([line for line in values if re.match(r"^\s*\d+\.\s+.+$", line)])


def field(block, name):
    labels = FIELD_ALIASES.get(name, (name,))
    pattern = "|".join(re.escape(item) for item in labels)
    match = re.search(rf"(?im)^-\s*(?:{pattern}):\s*(.+)$", block)
    return match.group(1).strip() if match else ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir")
    args = parser.parse_args()
    root = Path(args.case_dir)
    points_path, cases_path = root / "03-test-points.md", root / "04-test-cases.md"
    errors, warnings = [], []
    if not points_path.exists(): errors.append("missing 03-test-points.md")
    if not cases_path.exists(): errors.append("missing 04-test-cases.md")
    if errors:
        print("\n".join("ERROR: " + e for e in errors)); raise SystemExit(1)
    points, cases = points_path.read_text(encoding="utf-8"), cases_path.read_text(encoding="utf-8")
    if re.search(r"(?im)^status:\s*pending_confirmation\s*$", points):
        errors.append("test points are pending_confirmation")
    p0_ids = set()
    in_p0 = False
    for line in points.splitlines():
        if line.lower().startswith("###"):
            in_p0 = "p0" in line.lower()
        if in_p0:
            match = re.search(r"\b(TP[\w-]+)\b", line)
            if match: p0_ids.add(match.group(1))
    seen_titles, covered_points = set(), set()
    for case_id, title, block in blocks(cases):
        normalized = re.sub(r"\s+", " ", title).strip().lower()
        if normalized in seen_titles: errors.append(f"duplicate case title: {title}")
        seen_titles.add(normalized)
        for required in ("source_type", "source_reference", "coverage_type", "review_status", "case_status"):
            if not field(block, required): errors.append(f"{case_id}: missing {required}")
        point = field(block, "test_point")
        if point: covered_points.add(point)
        steps, results = numbered_count(block, "steps"), numbered_count(block, "expected_results")
        if not steps or steps != results: errors.append(f"{case_id}: steps ({steps}) and expected_results ({results}) must match")
        if field(block, "coverage_type") in ("regression", "回归") and not field(block, "historical_defect_reference"):
            errors.append(f"{case_id}: regression case lacks historical_defect_reference")
        if field(block, "review_status") in ("awaiting_confirmation", "待确认"):
            errors.append(f"{case_id}: unresolved rule cannot be a final case")
    missing_p0 = sorted(p0_ids - covered_points)
    if missing_p0: errors.append("uncovered P0 test points: " + ", ".join(missing_p0))
    if re.search(r"awaiting_confirmation", points, re.I):
        warnings.append("test points contain unresolved rules; ensure they are skipped or confirmed")
    for message in warnings: print("WARNING: " + message)
    for message in errors: print("ERROR: " + message)
    if errors: raise SystemExit(1)
    print("PASS: static quality gates passed")


if __name__ == "__main__":
    main()

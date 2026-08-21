#!/usr/bin/env python3
"""Calculate Markdown quality metrics for one case run."""
import argparse
from pathlib import Path


def rate(numerator, denominator):
    return None if denominator == 0 else numerator / denominator


def pct(value):
    return "not_available" if value is None else f"{value * 100:.1f}%"


def main():
    parser = argparse.ArgumentParser()
    for name in ("candidate", "adopted", "modified", "discarded", "executed", "passed", "p0-total", "p0-covered"):
        parser.add_argument(f"--{name}", type=int, default=0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    values = vars(args)
    if any(v < 0 for k, v in values.items() if k != "output"):
        parser.error("metrics must be non-negative")
    reviewed = args.adopted + args.modified + args.discarded
    if reviewed > args.candidate:
        parser.error("adopted + modified + discarded cannot exceed candidate")
    if args.passed > args.executed or args.p0_covered > args.p0_total:
        parser.error("passed and p0-covered cannot exceed their totals")

    adoption = rate(args.adopted, args.candidate)
    effectiveness = rate(args.passed, args.executed)
    p0_coverage = rate(args.p0_covered, args.p0_total)
    if p0_coverage is not None and p0_coverage < 1:
        gate, action = "block", "P0 coverage is incomplete; do not deliver final cases."
    elif adoption is None:
        gate, action = "pending", "Record adoption decisions before applying the adoption gate."
    elif adoption < 0.4:
        gate, action = "red", "Stop the generation pipeline and review inputs, rules, and prompts."
    elif adoption < 0.6:
        gate, action = "yellow", "Manual review is required before expansion."
    else:
        gate, action = "pass", "Adoption gate passed."
    text = f"""# Quality metrics\n\n- candidate: {args.candidate}\n- adopted: {args.adopted}\n- modified: {args.modified}\n- discarded: {args.discarded}\n- executed: {args.executed}\n- passed: {args.passed}\n- p0_total: {args.p0_total}\n- p0_covered: {args.p0_covered}\n- adoption_rate: {pct(adoption)}\n- execution_effectiveness: {pct(effectiveness)}\n- p0_coverage: {pct(p0_coverage)}\n- gate: {gate}\n- action: {action}\n"""
    Path(args.output).write_text(text, encoding="utf-8")
    print(f"gate={gate}; output={args.output}")


if __name__ == "__main__":
    main()

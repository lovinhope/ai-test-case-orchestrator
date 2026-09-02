"""Flask/Jinja2 host for the product/code challenge review stage."""

import json
import os
import secrets
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from .fixtures import ASSOCIATION_TEMPLATE, challenge_fixture


_SUBMIT_LOCK = threading.Lock()


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_case_path(case_root, case_id):
    if not case_id or case_id in {".", ".."} or any(ch in case_id for ch in "\\/:"):
        raise ValueError("case_id 无效")
    root = Path(case_root).resolve()
    case_dir = (root / case_id).resolve()
    if root != case_dir.parent:
        raise ValueError("case_id 超出允许目录")
    return case_dir


def _artifact_path(case_root, case_id, artifact_path):
    case_dir = _safe_case_path(case_root, case_id)
    expected = (Path("case") / case_id / "02-review.md").as_posix()
    if artifact_path != expected:
        raise ValueError("artifact_path 必须指向当前案例的 02-review.md")
    return case_dir / "02-review.md"


def _find_existing_run(artifact, run_id):
    if not artifact.exists():
        return False
    return f"- run_id: {run_id}" in artifact.read_text(encoding="utf-8")


def _render_review_markdown(payload, fixture):
    question_by_id = {question["id"]: question for question in fixture["questions"]}
    lines = [
        "# 产品/代码对抗评审",
        "",
        f"- run_id: {payload['run_id']}",
        f"- stage: {payload['stage']}",
        f"- commit_id: {fixture['commit_id']}",
        f"- reviewer: {payload['reviewer']}",
        f"- submitted_at: {payload['submitted_at']}",
        "- status: awaiting_test_point_review",
        "",
        "## 评审结果",
        "",
    ]
    for item in payload["items"]:
        question = question_by_id[item["id"]]
        evidence = "; ".join(
            next(e["summary"] for e in fixture["evidence"] if e["id"] == evidence_id)
            for evidence_id in question["evidence_ids"]
        ) or "待补充"
        disposition = {
            "confirmed": ("测试点", "test_point"),
            "discarded": ("跳过", "skipped"),
            "irrelevant": ("跳过", "skipped"),
        }[item["decision"]]
        lines.extend(
            [
                f"### {item['number']} {item['title']}",
                f"<!-- finding_id: {item['id']}; commit_id: {fixture['commit_id']}; source_reference: {question['source_reference']}; disposition: {disposition[1]} -->",
                f"- 来源类型：{question['surface']}",
                f"- 来源及依据：{question['source_reference']}",
                f"- 证据：{evidence}",
                f"- 风险：{question['rationale']}",
                f"- 处置：{disposition[0]}",
                f"- 理由：{item['reason'] or item['response'] or '待补充'}",
                f"- 请确认：{question['rule']}；评审意见：{item['response'] or '待补充'}",
                "",
            ]
        )
    return "\n".join(lines)


def _validate_payload(data, fixture):
    if not isinstance(data, dict):
        raise ValueError("请求体必须是 JSON 对象")
    required = ("run_id", "stage", "artifact_path", "case_id", "items", "reviewer")
    missing = [name for name in required if name not in data]
    if missing:
        raise ValueError("缺少字段：" + ", ".join(missing))
    if data["stage"] != fixture["stage"] or data["case_id"] != fixture["case_id"]:
        raise ValueError("评审阶段或案例不匹配")
    if data["run_id"] != fixture["run_id"]:
        raise ValueError("评审运行编号不匹配")
    if not isinstance(data["run_id"], str) or not data["run_id"].strip():
        raise ValueError("run_id 无效")
    if not isinstance(data["reviewer"], str) or not data["reviewer"].strip():
        raise ValueError("请填写评审人")
    if not isinstance(data["items"], list) or len(data["items"]) != len(fixture["questions"]):
        raise ValueError("必须提交全部评审问题")
    expected_ids = {item["id"] for item in fixture["questions"]}
    seen = set()
    for item in data["items"]:
        if not isinstance(item, dict):
            raise ValueError("问题结果格式无效")
        item_id = item.get("id")
        if item_id not in expected_ids or item_id in seen:
            raise ValueError("问题 ID 无效或重复")
        seen.add(item_id)
        decision = item.get("decision")
        if decision not in {"confirmed", "discarded", "irrelevant"}:
            raise ValueError("每个问题必须明确选择确认、废弃或不相关")
        response = item.get("response", "")
        reason = item.get("reason", "")
        if not isinstance(response, str) or not isinstance(reason, str):
            raise ValueError("回答和原因必须是文本")
        if decision == "confirmed" and not response.strip():
            raise ValueError("确认规则的问题必须填写具体规则")
        if decision != "confirmed" and not (response.strip() or reason.strip()):
            raise ValueError("废弃或不相关的问题必须填写说明")
    if seen != expected_ids:
        raise ValueError("必须提交全部评审问题")


def _run_next_module(app, fixture, review_path, case_dir):
    association_path = case_dir / "01-association.md"
    if not association_path.exists():
        association_path.write_text(
            ASSOCIATION_TEMPLATE.format(commit_id=fixture["commit_id"]), encoding="utf-8"
        )
    script = Path(app.config["TEST_POINT_SCRIPT"])
    command = [
        sys.executable,
        str(script),
        "--case-dir",
        str(case_dir),
        "--commit-id",
        fixture["commit_id"],
        "--association",
        str(association_path),
        "--review",
        str(review_path),
    ]
    return subprocess.run(command, capture_output=True, text=True, check=False)


def create_app(config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    repo_root = Path(__file__).resolve().parents[1]
    app.config.from_mapping(
        CASE_ROOT=str(repo_root / "web" / "runtime" / "cases"),
        TEST_POINT_SCRIPT=str(
            repo_root / "ai-test-point-generator" / "scripts" / "generate_test_points.py"
        ),
        VUE_SCRIPT_URL=os.getenv(
            "VUE_SCRIPT_URL", "https://unpkg.com/vue@3.5.18/dist/vue.global.prod.js"
        ),
        REVIEW_CSRF_TOKEN=secrets.token_urlsafe(24),
    )
    if config:
        app.config.update(config)
    Path(app.config["CASE_ROOT"]).mkdir(parents=True, exist_ok=True)

    @app.get("/reviews/challenge")
    def challenge_review():
        model = challenge_fixture()
        model["bridge_available"] = True
        model["vue_script_url"] = app.config["VUE_SCRIPT_URL"]
        model["csrf_token"] = app.config["REVIEW_CSRF_TOKEN"]
        return render_template("challenge_review.html", model=model)

    @app.post("/api/reviews/challenge/submit")
    def submit_challenge_review():
        fixture = challenge_fixture()
        data = request.get_json(silent=True)
        if request.headers.get("X-CSRF-Token") != app.config["REVIEW_CSRF_TOKEN"]:
            return jsonify({"accepted": False, "error": "CSRF token 无效或缺失"}), 403
        try:
            _validate_payload(data, fixture)
            review_path = _artifact_path(
                app.config["CASE_ROOT"], data["case_id"], data["artifact_path"]
            )
        except (ValueError, TypeError, KeyError) as exc:
            return jsonify({"accepted": False, "error": str(exc)}), 400

        with _SUBMIT_LOCK:
            case_dir = review_path.parent
            case_dir.mkdir(parents=True, exist_ok=True)
            if _find_existing_run(review_path, data["run_id"]):
                return jsonify(
                    {
                        "accepted": True,
                        "persisted_artifact": str(review_path),
                        "next_stage": "test_point_review",
                        "idempotent": True,
                    }
                )
            data["submitted_at"] = data.get("submitted_at") or _utc_now()
            review_path.write_text(_render_review_markdown(data, fixture), encoding="utf-8")
            result = _run_next_module(app, fixture, review_path, case_dir)
            if result.returncode != 0:
                return (
                    jsonify(
                        {
                            "accepted": False,
                            "error": "评审已保存，但下一模块启动失败",
                            "persisted_artifact": str(review_path),
                            "detail": result.stderr[-2000:],
                        }
                    ),
                    502,
                )
        return jsonify(
            {
                "accepted": True,
                "persisted_artifact": str(review_path),
                "next_stage": "test_point_review",
            }
        )

    @app.get("/api/reviews/challenge/model")
    def review_model():
        return app.response_class(
            json.dumps(challenge_fixture(), ensure_ascii=False), mimetype="application/json"
        )

    return app


if __name__ == "__main__":
    create_app().run(debug=True)

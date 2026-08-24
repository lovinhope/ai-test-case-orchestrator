import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from web.app import create_app
from web.fixtures import challenge_fixture


class ChallengeReviewTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.case_root = Path(self.temp_dir.name) / "cases"
        self.app = create_app(
            {
                "TESTING": True,
                "CASE_ROOT": str(self.case_root),
                "TEST_POINT_SCRIPT": str(Path(self.temp_dir.name) / "generate.py"),
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def payload(self, decisions=None):
        fixture = challenge_fixture()
        decisions = decisions or ["confirmed"] * len(fixture["questions"])
        return {
            "run_id": fixture["run_id"],
            "stage": fixture["stage"],
            "case_id": fixture["case_id"],
            "artifact_path": fixture["artifact_path"],
            "reviewer": "tester",
            "items": [
                {
                    "id": question["id"],
                    "number": question["number"],
                    "title": question["title"],
                    "response": "确认规则内容" if decision == "confirmed" else "",
                    "reason": "本次测试不覆盖旧入口" if decision != "confirmed" else "",
                    "decision": decision,
                }
                for question, decision in zip(fixture["questions"], decisions)
            ],
        }

    def post_payload(self, payload):
        return self.client.post(
            "/api/reviews/challenge/submit",
            json=payload,
            headers={"X-CSRF-Token": self.app.config["REVIEW_CSRF_TOKEN"]},
        )

    def test_server_renders_evidence_and_questions_without_vue(self):
        response = self.client.get("/reviews/challenge")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("权限范围业务规则", body)
        self.assertIn("Q01", body)
        self.assertIn("当前页面仍可阅读", body)

    @patch("web.app.subprocess.run")
    def test_valid_submission_persists_then_runs_next_module(self, run):
        run.return_value.returncode = 0
        response = self.post_payload(self.payload())
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["next_stage"], "test_point_review")
        artifact = self.case_root / "demo-challenge" / "02-review.md"
        self.assertTrue(artifact.exists())
        self.assertIn("status: awaiting_test_point_review", artifact.read_text(encoding="utf-8"))
        run.assert_called_once()
        self.assertEqual(run.call_args.kwargs["check"], False)

    def test_confirmed_question_requires_answer(self):
        data = self.payload()
        data["items"][0]["response"] = ""
        response = self.post_payload(data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("必须填写具体规则", response.get_json()["error"])

    def test_real_next_module_creates_pending_test_point_artifact(self):
        self.app.config["TEST_POINT_SCRIPT"] = str(
            Path(__file__).resolve().parents[2]
            / "ai-test-point-generator"
            / "scripts"
            / "generate_test_points.py"
        )
        response = self.post_payload(self.payload())
        self.assertEqual(response.status_code, 200)
        test_points = self.case_root / "demo-challenge" / "03-test-points.md"
        self.assertTrue(test_points.exists())
        self.assertIn("pending_confirmation", test_points.read_text(encoding="utf-8"))

    @patch("web.app.subprocess.run")
    def test_discarded_and_irrelevant_questions_are_allowed_with_reason(self, run):
        run.return_value.returncode = 0
        response = self.post_payload(self.payload(["discarded", "irrelevant", "confirmed"]))
        self.assertEqual(response.status_code, 200)
        artifact = self.case_root / "demo-challenge" / "02-review.md"
        text = artifact.read_text(encoding="utf-8")
        self.assertIn("decision: discarded", text)
        self.assertIn("decision: irrelevant", text)

    @patch("web.app.subprocess.run")
    def test_duplicate_submission_is_idempotent(self, run):
        run.return_value.returncode = 0
        first = self.post_payload(self.payload())
        second = self.post_payload(self.payload())
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.get_json()["idempotent"])
        run.assert_called_once()

    @patch("web.app.subprocess.run")
    def test_downstream_failure_keeps_artifact_but_does_not_advance(self, run):
        run.return_value.returncode = 1
        run.return_value.stderr = "generator failed"
        response = self.post_payload(self.payload())
        self.assertEqual(response.status_code, 502)
        self.assertFalse(response.get_json()["accepted"])
        self.assertTrue((self.case_root / "demo-challenge" / "02-review.md").exists())


if __name__ == "__main__":
    unittest.main()

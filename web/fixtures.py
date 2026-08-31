"""Replaceable server-side fixture for the first challenge-review screen."""


def challenge_fixture():
    return {
        "run_id": "run-demo-001",
        "stage": "challenge_review",
        "case_id": "demo-challenge",
        "commit_id": "e3164e4008896f2c69ab0508b4fa05fcfdb5c1ae",
        "reviewer": "",
        "artifact_path": "case/demo-challenge/02-review.md",
        "evidence": [
            {
                "id": "business-rule-001",
                "number": "E01",
                "title": "权限范围业务规则",
                "summary": "确认页面入口、产品范围和策略范围是否由当前用户权限共同决定。",
                "source_type": "business_knowledge",
                "updated_at": "2026-08-20",
                "source_url": "https://example.invalid/knowledge/permission-scope",
                "association_reason": "支持产品权限规则",
            },
            {
                "id": "code-change-001",
                "number": "E02",
                "title": "已验证代码变更",
                "summary": "代码变更包含入口校验、异常分支和下游持久化调用，需要确认业务期望与实现是否一致。",
                "source_type": "source_code",
                "updated_at": "2026-08-21",
                "source_url": "https://example.invalid/code/commit/e3164e4",
                "association_reason": "证明接口分支与异常处理",
            },
        ],
        "questions": [
            {
                "id": "P-01",
                "number": "Q01",
                "title": "页面可见范围",
                "surface": "产品规则",
                "rule": "请确认哪些用户、角色、产品和策略可以看到该页面入口。",
                "evidence_ids": ["business-rule-001"],
                "source_reference": "业务规则：权限范围",
                "rationale": "缺少具体范围会导致正向和越权场景无法形成可执行测试点。",
                "disposition": "awaiting_confirmation",
            },
            {
                "id": "C-01",
                "number": "Q02",
                "title": "异常处理结果",
                "surface": "代码/接口规则",
                "rule": "当下游持久化失败时，页面和接口应返回什么结果，是否允许进入下一阶段？",
                "evidence_ids": ["code-change-001"],
                "source_reference": "代码变更：入口与持久化调用",
                "rationale": "需要明确失败时的可观察结果和阶段流转边界。",
                "disposition": "awaiting_confirmation",
            },
            {
                "id": "I-01",
                "number": "Q03",
                "title": "兼容性问题",
                "surface": "集成规则",
                "rule": "请确认历史页面或旧权限字段是否仍属于本次测试范围。",
                "evidence_ids": ["business-rule-001", "code-change-001"],
                "source_reference": "业务规则与代码关联",
                "rationale": "如果旧入口不再支持，应明确标记为废弃或本次测试不相关。",
                "disposition": "awaiting_confirmation",
            },
        ],
    }


ASSOCIATION_TEMPLATE = """# Association\n\n- commit_id: {commit_id}\n- status: retained_fixture\n\n## Business evidence\n\n- fixture: server-side challenge review demo\n\n## Code evidence\n\n- fixture: server-side challenge review demo\n"""

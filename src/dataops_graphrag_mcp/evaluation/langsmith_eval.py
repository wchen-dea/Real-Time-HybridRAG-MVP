from typing import Any

from langsmith import traceable

from dataops_graphrag_mcp.langgraph_orchestrator.supervisor import (
    DataOpsLangGraphSupervisor,
)


@traceable(run_type="chain", name="dataops_langgraph_eval_case")
def evaluate_case(
    supervisor: DataOpsLangGraphSupervisor,
    question: str,
    expected_keywords: list[str] | None = None,
    user_id: str | None = "eval-user",
    environment: str | None = "eval",
) -> dict[str, Any]:
    response = supervisor.invoke(question, user_id=user_id, environment=environment)
    keywords = expected_keywords or []
    answer = str(response.get("answer", "")).lower()
    keyword_hits = [keyword for keyword in keywords if keyword.lower() in answer]
    score = 1.0 if not keywords else len(keyword_hits) / len(keywords)

    return {
        "question": question,
        "expected_keywords": keywords,
        "matched_keywords": keyword_hits,
        "score": score,
        "response": response,
    }


@traceable(run_type="chain", name="dataops_langgraph_eval_suite")
def run_evaluation_suite(cases: list[dict[str, Any]]) -> dict[str, Any]:
    supervisor = DataOpsLangGraphSupervisor()
    results = []

    for case in cases:
        results.append(
            evaluate_case(
                supervisor=supervisor,
                question=case["question"],
                expected_keywords=case.get("expected_keywords", []),
                user_id=case.get("user_id", "eval-user"),
                environment=case.get("environment", "eval"),
            )
        )

    avg_score = sum(float(r["score"]) for r in results) / max(len(results), 1)
    return {
        "total_cases": len(results),
        "average_score": avg_score,
        "results": results,
    }

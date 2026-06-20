from typing import Any

from langsmith import traceable

from dataops_graphrag_mcp.langgraph_orchestrator.supervisor import (
    DataOpsLangGraphSupervisor,
)


def _retrieval_recall(
    vector_results: list[dict],
    expected_source_ids: list[str],
) -> float:
    """Fraction of expected source IDs found in the top-k vector results."""
    if not expected_source_ids:
        return 1.0
    returned_ids = {str(r.get("chunk_id", "")) for r in vector_results}
    hits = sum(1 for sid in expected_source_ids if sid in returned_ids)
    return hits / len(expected_source_ids)


def _factuality_score(answer: str, evidence: list[dict]) -> float:
    """
    Lightweight keyword-overlap factuality proxy.
    Measures what fraction of the non-trivial words in the answer
    appear in at least one evidence chunk_text field.
    A score of 1.0 means every answer word is grounded in evidence.
    """
    stop = {
        "the", "a", "an", "is", "are", "was", "were", "of", "to", "in",
        "and", "or", "for", "with", "that", "this", "it", "be", "as", "at",
    }
    answer_words = [
        w.lower().strip(".,;:?!")
        for w in answer.split()
        if len(w) > 3 and w.lower() not in stop
    ]
    if not answer_words:
        return 1.0
    evidence_text = " ".join(
        str(e.get("chunk_text", "")).lower() for e in evidence if isinstance(e, dict)
    )
    grounded = sum(1 for w in answer_words if w in evidence_text)
    return grounded / len(answer_words)


@traceable(run_type="chain", name="dataops_langgraph_eval_case")
def evaluate_case(
    supervisor: DataOpsLangGraphSupervisor,
    question: str,
    expected_keywords: list[str] | None = None,
    expected_source_ids: list[str] | None = None,
    user_id: str | None = "eval-user",
    environment: str | None = "eval",
) -> dict[str, Any]:
    response = supervisor.invoke(question, user_id=user_id, environment=environment)

    # Keyword match score
    keywords = expected_keywords or []
    answer = str(response.get("answer", "")).lower()
    keyword_hits = [kw for kw in keywords if kw.lower() in answer]
    keyword_score = 1.0 if not keywords else len(keyword_hits) / len(keywords)

    # Retrieval recall score
    vector_results = [
        e if isinstance(e, dict) else vars(e)
        for e in response.get("evidence", [])
    ]
    recall = _retrieval_recall(vector_results, expected_source_ids or [])

    # Factuality proxy score
    factuality = _factuality_score(answer, vector_results)

    # Weighted composite score: keyword 40%, recall 30%, factuality 30%
    composite = round(0.4 * keyword_score + 0.3 * recall + 0.3 * factuality, 4)

    return {
        "question": question,
        "expected_keywords": keywords,
        "matched_keywords": keyword_hits,
        "keyword_score": round(keyword_score, 4),
        "retrieval_recall": round(recall, 4),
        "factuality_score": round(factuality, 4),
        "composite_score": composite,
        "quality_gate_passed": response.get("quality_gate_passed"),
        "confidence": response.get("confidence"),
        "prompt_version": response.get("prompt_version"),
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
                expected_source_ids=case.get("expected_source_ids", []),
                user_id=case.get("user_id", "eval-user"),
                environment=case.get("environment", "eval"),
            )
        )

    avg_keyword = sum(r["keyword_score"] for r in results) / max(len(results), 1)
    avg_recall = sum(r["retrieval_recall"] for r in results) / max(len(results), 1)
    avg_factuality = sum(r["factuality_score"] for r in results) / max(len(results), 1)
    avg_composite = sum(r["composite_score"] for r in results) / max(len(results), 1)

    return {
        "total_cases": len(results),
        "average_keyword_score": round(avg_keyword, 4),
        "average_retrieval_recall": round(avg_recall, 4),
        "average_factuality_score": round(avg_factuality, 4),
        "average_composite_score": round(avg_composite, 4),
        "results": results,
    }


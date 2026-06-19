from typing import Any, Literal, TypedDict

RetrievalMode = Literal["vector", "graph", "sql", "hybrid"]


class DataOpsAgentState(TypedDict, total=False):
    question: str
    user_id: str | None
    environment: str | None
    retrieval_mode: RetrievalMode
    extracted_entities: dict[str, Any]
    target_entity_name: str | None
    vector_results: list[dict[str, Any]]
    graph_results: list[dict[str, Any]]
    sql_results: list[dict[str, Any]]
    evidence: list
    graph_path: list
    final_answer: str
    confidence: float
    recommended_next_actions: list[str]
    missing_evidence_warnings: list[str]
    quality_gate_passed: bool

from dataops_graphrag_mcp.common.settings import settings
from dataops_graphrag_mcp.common.langsmith import (
    configure_langsmith,
    is_langsmith_enabled,
    langsmith_tags,
)
from dataops_graphrag_mcp.langgraph_orchestrator.graph import build_dataops_langgraph
from langsmith import traceable


class DataOpsLangGraphSupervisor:
    def __init__(self):
        configure_langsmith()
        self.graph = build_dataops_langgraph()

    @traceable(run_type="chain", name="dataops_langgraph_supervisor_invoke")
    def invoke(
        self, question: str, user_id: str | None = None, environment: str | None = None
    ) -> dict:
        graph_config = {
            "metadata": {
                "app_env": settings.app_env,
                "user_id": user_id,
                "environment": environment,
            },
            "tags": langsmith_tags(environment),
        }
        result = self.graph.invoke(
            {"question": question, "user_id": user_id, "environment": environment},
            config=graph_config if is_langsmith_enabled() else None,
        )
        return {
            "answer": result.get("final_answer"),
            "confidence": result.get("confidence"),
            "retrieval_mode": result.get("retrieval_mode"),
            "extracted_entities": result.get("extracted_entities"),
            "evidence": [
                e.model_dump() if hasattr(e, "model_dump") else e
                for e in result.get("evidence", [])
            ],
            "graph_path": [
                g.model_dump() if hasattr(g, "model_dump") else g
                for g in result.get("graph_path", [])
            ],
            "recommended_next_actions": result.get("recommended_next_actions", []),
            "missing_evidence_warnings": result.get("missing_evidence_warnings", []),
            "quality_gate_passed": result.get("quality_gate_passed"),
            "model_metadata": {
                "provider": settings.llm_provider,
                "model": settings.anthropic_model,
            },
        }

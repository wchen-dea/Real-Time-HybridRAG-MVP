from fastapi import FastAPI
from dataops_graphrag_mcp.langgraph_orchestrator.supervisor import (
    DataOpsLangGraphSupervisor,
)

app = FastAPI(title="Real-Time HybridRAG MVP")
supervisor = DataOpsLangGraphSupervisor()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask")
def ask(payload: dict) -> dict:
    return supervisor.invoke(
        payload["question"], payload.get("user_id"), payload.get("environment")
    )

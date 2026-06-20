import time
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from dataops_graphrag_mcp.common.logging import get_logger, new_correlation_id
from dataops_graphrag_mcp.llm.guardrails import check_input
from dataops_graphrag_mcp.langgraph_orchestrator.supervisor import (
    DataOpsLangGraphSupervisor,
)

app = FastAPI(title="Real-Time HybridRAG Minimum Viable Product (MVP)")
supervisor = DataOpsLangGraphSupervisor()
_log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Simple in-process token-bucket rate limiter (report §5: API rate limiting).
# Replace with Redis-backed middleware in multi-replica deployments.
# ---------------------------------------------------------------------------
_RATE_LIMIT_REQUESTS = 60   # max requests per window
_RATE_LIMIT_WINDOW = 60     # window in seconds
_request_counts: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(client_ip: str) -> None:
    now = time.monotonic()
    window_start = now - _RATE_LIMIT_WINDOW
    timestamps = [t for t in _request_counts[client_ip] if t > window_start]
    timestamps.append(now)
    _request_counts[client_ip] = timestamps
    if len(timestamps) > _RATE_LIMIT_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")


@app.middleware("http")
async def _attach_correlation_id(request: Request, call_next):
    """Assign a correlation ID to every request and echo it in the response."""
    cid = request.headers.get("X-Correlation-ID") or new_correlation_id()
    request.state.correlation_id = cid
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask")
def ask(payload: dict, request: Request) -> JSONResponse:
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    question = payload.get("question", "")

    # Guardrail: screen input before invoking the pipeline (report §5)
    guard = check_input(question)
    if not guard["safe"]:
        _log.warning("Guardrail blocked request: %s", guard["reason"])
        raise HTTPException(status_code=400, detail=f"Request blocked: {guard['reason']}")

    result = supervisor.invoke(
        question, payload.get("user_id"), payload.get("environment")
    )
    return JSONResponse(
        content=result,
        headers={"X-Correlation-ID": getattr(request.state, "correlation_id", "")},
    )


from dataops_graphrag_mcp.hybrid.query_router import QueryRouter
from dataops_graphrag_mcp.langgraph_orchestrator.supervisor import (
    DataOpsLangGraphSupervisor,
)
from dataops_graphrag_mcp.mcp_server.server import server


def test_router():
    assert QueryRouter().route("Find the runbook for Kafka lag").value in [
        "vector",
        "hybrid",
    ]


def test_langgraph_without_api_key():
    assert "answer" in DataOpsLangGraphSupervisor().invoke(
        "Find the runbook for Kafka lag.", environment="dev"
    )


def test_mcp_registry():
    assert "dataops_agent_tool" in server.list_tools()

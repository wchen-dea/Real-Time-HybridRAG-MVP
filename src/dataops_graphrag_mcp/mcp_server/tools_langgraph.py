from dataops_graphrag_mcp.langgraph_orchestrator.supervisor import (
    DataOpsLangGraphSupervisor,
)

_supervisor = DataOpsLangGraphSupervisor()


def dataops_agent_tool(
    question: str, user_id: str | None = None, environment: str | None = None
) -> dict:
    return _supervisor.invoke(question, user_id, environment)

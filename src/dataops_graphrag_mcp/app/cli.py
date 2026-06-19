from dataops_graphrag_mcp.langgraph_orchestrator.supervisor import (
    DataOpsLangGraphSupervisor,
)

if __name__ == "__main__":
    print(
        DataOpsLangGraphSupervisor().invoke(
            "Find the runbook for Kafka lag.", environment="dev"
        )
    )

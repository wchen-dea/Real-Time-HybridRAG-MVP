from dataops_graphrag_mcp.common.settings import settings
from dataops_graphrag_mcp.mcp_server.tools_langgraph import dataops_agent_tool


class DataOpsMcpServer:
    def __init__(self, name: str):
        self.name = name
        self.tools = {"dataops_agent_tool": dataops_agent_tool}

    def list_tools(self) -> list[str]:
        return list(self.tools.keys())

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        return self.tools[tool_name](**arguments)


server = DataOpsMcpServer(settings.mcp_server_name)
if __name__ == "__main__":
    print(f"Starting MCP server facade: {server.name}")
    for tool in server.list_tools():
        print(f" - {tool}")

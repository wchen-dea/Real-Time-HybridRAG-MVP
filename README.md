# Real-Time HybridRAG MVP

Full sample Data & AI MVP using **VectorRAG + GraphRAG + LangGraph + MCP Server + Anthropic Claude + Databricks AI Search + Neo4j + EKS deployment skeleton**.

## Main workflow

```text
MCP Client / Agent
  -> MCP Server dataops_agent_tool
  -> LangGraph Orchestrator
  -> VectorRAG / GraphRAG / Databricks SQL
  -> Anthropic Claude answer generation + quality gate
```

## Local setup

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m dataops_graphrag_mcp.mcp_server.server
python -m dataops_graphrag_mcp.app.cli
```

## Optional bootstrap commands

```bash
python -m dataops_graphrag_mcp.vectorrag.bootstrap_ai_search
python -m dataops_graphrag_mcp.graphrag.populate_from_metadata
uvicorn dataops_graphrag_mcp.app.api:app --reload
```

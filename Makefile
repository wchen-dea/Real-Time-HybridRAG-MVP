.PHONY: install test run api bootstrap-vector bootstrap-graph
install:
	pip install -e ".[dev]"
test:
	pytest -q
run:
	python -m dataops_graphrag_mcp.mcp_server.server
api:
	uvicorn dataops_graphrag_mcp.app.api:app --reload
bootstrap-vector:
	python -m dataops_graphrag_mcp.vectorrag.bootstrap_ai_search
bootstrap-graph:
	python -m dataops_graphrag_mcp.graphrag.populate_from_metadata

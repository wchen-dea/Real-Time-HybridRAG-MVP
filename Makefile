.PHONY: install test run api bootstrap-vector bootstrap-graph realtime-producer streaming-up streaming-down streaming-topics connectors-render connectors-deploy
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
realtime-producer:
	python -m dataops_graphrag_mcp.ingestion.realtime_event_producer
streaming-up:
	docker compose -f deploy/docker/docker-compose.streaming.yml up -d
streaming-down:
	docker compose -f deploy/docker/docker-compose.streaming.yml down
streaming-topics:
	bash scripts/init_kafka_topics.sh
connectors-render:
	python scripts/deploy_connectors.py
connectors-deploy:
	python scripts/deploy_connectors.py --register

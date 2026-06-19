# Real-Time HybridRAG MVP

Full sample Data & AI MVP using **VectorRAG + GraphRAG + LangGraph + MCP Server + Anthropic Claude + Databricks AI Search + Neo4j + EKS deployment skeleton**.

## What this repository provides

1. Hybrid retrieval across vector and graph context.
2. LangGraph-based orchestration for tool routing and answer generation.
3. MCP server interface for agent-driven workflows.
4. Deployment assets for production-style operation on AWS EKS.

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

## Real-time event pipeline (Confluent Kafka + Flink + Kafka Connect)

Topology:

```text
Producer -> KAFKA_RAW_TOPIC
Flink SQL enrich/format -> KAFKA_ENRICHED_VECTOR_TOPIC + KAFKA_ENRICHED_GRAPH_TOPIC
Kafka Connect sinks -> Databricks document_chunks + Neo4j graph
```

Local stack bootstrap:

```bash
make streaming-up
make streaming-topics
```

### 1) Produce ever-changing source events

```bash
python -m dataops_graphrag_mcp.ingestion.realtime_event_producer
```

Equivalent Make target:

```bash
make realtime-producer
```

### 2) Run Flink transform job

Use:

1. resources/jobs/flink_realtime_hybrid_updates.sql

This consumes `KAFKA_RAW_TOPIC` and publishes two enriched topics:

1. `KAFKA_ENRICHED_VECTOR_TOPIC`
2. `KAFKA_ENRICHED_GRAPH_TOPIC`

### 3) Deploy Kafka Connect sink connectors

Connector templates:

1. resources/connectors/templates/vector_sink_databricks_jdbc.tmpl.json
2. resources/connectors/templates/graph_sink_neo4j.tmpl.json

One command (render templates + register connectors):

```bash
make connectors-deploy
```

Render only:

```bash
make connectors-render
```

Register connectors (example):

```bash
curl -X POST http://localhost:8083/connectors \
  -H 'Content-Type: application/json' \
  --data @resources/connectors/generated/vector_sink_databricks_jdbc.json

curl -X POST http://localhost:8083/connectors \
  -H 'Content-Type: application/json' \
  --data @resources/connectors/generated/graph_sink_neo4j.json
```

Raw event shape (producer output):

```json
{
  "event_id": "evt-123",
  "op": "upsert",
  "event_time": "2026-06-19T12:00:00Z",
  "pipeline": "kafka_to_delta",
  "flink_application": "lineage-job",
  "kafka_topic": "ops.lineage",
  "schema_subject": "ops.lineage-value",
  "delta_table": "ai_context.graph_nodes",
  "snowflake_object": "ANALYTICS.GRAPH_NODES",
  "dashboard": "Lineage Dashboard",
  "owner_team": "data-platform",
  "chunk_id": "chunk-001",
  "chunk_text": "Kafka lag handling runbook",
  "title": "Kafka Runbook",
  "source_name": "kafka_producer",
  "source_uri": "kafka://ops.lineage/chunk-001",
  "domain": "operations",
  "system_name": "kafka",
  "environment": "dev"
}
```

Flink-enriched vector topic event shape:

```json
{
  "event_id": "evt-123",
  "op": "upsert",
  "event_time": "2026-06-19T12:00:00.000Z",
  "chunk_id": "chunk-001",
  "source_type": "stream",
  "source_name": "flink_stream",
  "source_uri": "kafka://ops.lineage/chunk-001",
  "title": "Kafka Runbook",
  "chunk_text": "Kafka lag handling runbook",
  "domain": "operations",
  "system_name": "kafka",
  "environment": "dev",
  "owner_team": "data-platform"
}
```

Flink-enriched graph topic event shape:

```json
{
  "event_id": "evt-123",
  "op": "upsert",
  "event_time": "2026-06-19T12:00:00.000Z",
  "pipeline": "kafka_to_delta",
  "flink_application": "lineage-job",
  "kafka_topic": "ops.lineage",
  "schema_subject": "ops.lineage-value",
  "delta_table": "ai_context.graph_nodes",
  "snowflake_object": "ANALYTICS.GRAPH_NODES",
  "dashboard": "Lineage Dashboard",
  "owner_team": "data-platform",
  "environment": "dev"
}
```

## Production deployment on AWS EKS

For a production-oriented deployment introduction and run sequence, see:

1. docs/production_deployment_aws_eks.md

## Operations and planning docs

1. runbook.md
2. docs/cost_model.md
3. docs/all_3_additions_summary.md

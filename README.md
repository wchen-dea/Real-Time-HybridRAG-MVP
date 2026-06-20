# Real-Time HybridRAG Minimum Viable Product (MVP)

Production-oriented Data and AI Minimum Viable Product (MVP) combining VectorRAG, GraphRAG, LangGraph orchestration, MCP tool serving, Databricks AI Search, and Neo4j.

## What This Repository Provides

- Hybrid retrieval across vector and graph context.
- LangGraph orchestration for routing and answer generation.
- MCP tool interface for agent workflows.
- Deployment assets for AWS EKS.

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Language and Runtime | Python 3.11, Java 17 (Flink UDF) |
| Application Framework | FastAPI, LangGraph, MCP |
| LLM and Evaluation | Anthropic Claude, LangSmith |
| Retrieval and Data | Databricks AI Search, Databricks SQL, Neo4j |
| Streaming | Confluent Kafka, Flink SQL, Kafka Connect |
| Packaging and Build | pip/uv, Maven (flink-embedding-udf) |
| Infrastructure | Docker, Kubernetes, AWS EKS, IRSA |

## End-to-End Workflow

```text
MCP Client / Agent
  -> MCP Server dataops_agent_tool
  -> LangGraph Orchestrator
  -> VectorRAG / GraphRAG / Databricks SQL
  -> Anthropic Claude answer generation + quality gate
```

## Documentation Map

- [Architecture](docs/architecture.md)
- [Runbook](docs/runbook.md)
- [Production Deployment on AWS EKS](docs/deployment.md)
- [Cost Model](docs/cost_model.md)
- [Connector Guide](resources/connectors/README.md)

## Local Setup

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the MCP tool service:

```bash
python -m dataops_graphrag_mcp.mcp_server.server
```

Optional API and CLI entrypoints:

```bash
uvicorn dataops_graphrag_mcp.app.api:app --reload
python -m dataops_graphrag_mcp.app.cli
```

## Data Bootstrap Commands

```bash
python -m dataops_graphrag_mcp.vectorrag.bootstrap_ai_search
python -m dataops_graphrag_mcp.graphrag.populate_from_metadata
```

## LangSmith Monitoring and Evaluation

Set the following in `.env`:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-langsmith-api-key>
LANGSMITH_PROJECT=real-time-hybridrag-mvp
LANGSMITH_TAGS=hybridrag,mvp,monitoring
```

With tracing enabled, API, CLI, and MCP calls are monitored through `DataOpsLangGraphSupervisor.invoke`.

Run a traced evaluation suite:

```python
from dataops_graphrag_mcp.evaluation import run_evaluation_suite

cases = [
    {
        "question": "Find the runbook for Kafka lag.",
        "expected_keywords": ["runbook", "kafka"],
    },
    {
        "question": "What lineage is impacted by table X?",
        "expected_keywords": ["lineage"],
    },
]

summary = run_evaluation_suite(cases)
print(summary["average_score"])
```

## Real-Time Event Pipeline

Topology:

```text
Producer -> KAFKA_RAW_TOPIC
Flink SQL enrich/format -> KAFKA_ENRICHED_VECTOR_TOPIC + KAFKA_ENRICHED_GRAPH_TOPIC
Kafka Connect sinks -> Databricks document_chunks + Neo4j graph
```

Start local streaming stack:

```bash
make streaming-up
make streaming-topics
```

Produce source events:

```bash
python -m dataops_graphrag_mcp.ingestion.realtime_event_producer
```

Equivalent Make target:

```bash
make realtime-producer
```

Run Flink transform job (requires `flink-embedding-udf.jar` on the Flink cluster classpath — see [flink-embedding-udf/](flink-embedding-udf/)):

- [Flink job SQL](resources/jobs/flink_realtime_hybrid_updates.sql)

Deploy Kafka Connect sinks:

- [Vector sink template](resources/connectors/templates/vector_sink_databricks_jdbc.tmpl.json)
- [Graph sink template](resources/connectors/templates/graph_sink_neo4j.tmpl.json)

```bash
make connectors-deploy
```

Render connector files only:

```bash
make connectors-render
```

Manual registration example:

```bash
curl -X POST http://localhost:8083/connectors \
  -H 'Content-Type: application/json' \
  --data @resources/connectors/generated/vector_sink_databricks_jdbc.json

curl -X POST http://localhost:8083/connectors \
  -H 'Content-Type: application/json' \
  --data @resources/connectors/generated/graph_sink_neo4j.json
```

## Sample Event Shapes

Raw producer event:

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

Flink-enriched vector event (includes pre-computed embedding vector):

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
  "embedding": [0.021, -0.043, 0.117, "..."],
  "domain": "operations",
  "system_name": "kafka",
  "environment": "dev",
  "owner_team": "data-platform"
}
```

Flink-enriched graph event:

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

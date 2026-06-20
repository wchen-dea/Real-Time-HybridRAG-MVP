# Runbook: Real-Time HybridRAG Minimum Viable Product (MVP)

## Quick Links

- [README](../README.md)
- [Tech Stack](../README.md#tech-stack)
- [Architecture](architecture.md)
- [Production Deployment](deployment.md)
- [Cost Model](cost_model.md)

## Purpose

This runbook defines standard operating procedures for running, deploying, and troubleshooting the Real-Time HybridRAG Minimum Viable Product (MVP) service.

## Scope

Applies to:

1. Local development and validation.
2. Databricks bootstrap jobs for vector and graph data.
3. Production-style deployment on AWS EKS.
4. Basic incident response and rollback.

## Service Overview

Main components:

- MCP server entrypoint in src/dataops_graphrag_mcp/mcp_server/server.py
- LangGraph orchestration in src/dataops_graphrag_mcp/langgraph_orchestrator/
- Vector retrieval in src/dataops_graphrag_mcp/vectorrag/
- Graph retrieval in src/dataops_graphrag_mcp/graphrag/
- Input guardrails in src/dataops_graphrag_mcp/llm/guardrails.py
- Response caching and structured logging in supervisor and common/logging.py
- Deployment manifests in deploy/k8s/
- Databricks jobs in resources/jobs/

## Standard Operating Rhythm

1. Daily: Check service health, error rates, and dependency status.
2. Weekly: Review deployment drift, unresolved alerts, and recovery posture.
3. Monthly: Run cost review using [Cost Model](cost_model.md) and update action items.

## Prerequisites

1. Python 3.11+
2. uv or pip for dependency management
3. Access credentials for:
   - Databricks workspace and SQL endpoint
   - Anthropic API
   - Neo4j or Neptune
4. For EKS operations: AWS CLI, kubectl, Docker, ECR access

## Environment Setup

1. Copy environment template:

```bash
cp .env.example .env
```

2. Install dependencies:

```bash
uv sync
```

Alternative:

```bash
pip install -e ".[dev]"
```

3. Validate tests:

```bash
pytest -q
```

## Local Run Procedures

Start MCP server:

```bash
python -m dataops_graphrag_mcp.mcp_server.server
```

Start API server (optional):

```bash
uvicorn dataops_graphrag_mcp.app.api:app --reload
```

Start CLI (optional):

```bash
python -m dataops_graphrag_mcp.app.cli
```

## Data Bootstrap Procedures

Run these when initializing or refreshing retrieval stores.

Vector bootstrap:

```bash
python -m dataops_graphrag_mcp.vectorrag.bootstrap_ai_search
```

Graph bootstrap:

```bash
python -m dataops_graphrag_mcp.graphrag.populate_from_metadata
```

Databricks job definitions:

- resources/jobs/ingest_documents.yml
- resources/jobs/build_vector_index.yml
- resources/jobs/build_graph.yml
- resources/jobs/deploy_mcp_langgraph.yml

Kafka Connect templates:

- resources/connectors/templates/vector_sink_databricks_jdbc.tmpl.json
- resources/connectors/templates/graph_sink_neo4j.tmpl.json

## Real-Time Stream Sync Procedures

Use Confluent Kafka as the event bus, Flink for enrichment, and Kafka Connect sinks for destination writes.

Reference Flink SQL starter:

- resources/jobs/flink_realtime_hybrid_updates.sql

The Flink job uses the `generate_embedding` UDF to compute embeddings at stream time.
Build and deploy the UDF JAR before submitting the job:

```bash
cd flink-embedding-udf && mvn clean package
# copy target/flink-embedding-udf.jar to the Flink cluster classpath
```

Reference connector templates:

- resources/connectors/templates/vector_sink_databricks_jdbc.tmpl.json
- resources/connectors/templates/graph_sink_neo4j.tmpl.json

Run producer (raw changing events):

```bash
python -m dataops_graphrag_mcp.ingestion.realtime_event_producer
```

Start local streaming infrastructure:

```bash
make streaming-up
make streaming-topics
```

Deploy connectors in one command:

```bash
make connectors-deploy
```

Operational checks:

1. Confirm raw topic throughput for `KAFKA_RAW_TOPIC`.
2. Confirm Flink consumer lag is stable and both enriched topics receive records.
3. Confirm embedding field is non-null in `hybridrag.enriched.vector` records (indicates UDF is active).
4. Confirm Kafka Connect vector sink writes to `AI_SEARCH_SOURCE_TABLE`.
5. Confirm Kafka Connect graph sink writes/upserts lineage in Neo4j.

## Production Deployment (AWS EKS)

Reference: [Production Deployment](deployment.md)

Recommended order:

1. Build and push container image.
2. Apply namespace and IRSA service account.
3. Apply configmap, deployment, and service manifests.
4. Apply environment-specific ingress from platform repo.
5. Run bootstrap jobs.
6. Perform post-deploy validation.

Core apply commands:

```bash
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/serviceaccount-irsa.yaml
kubectl apply -f deploy/k8s/configmap.yaml
kubectl apply -f deploy/k8s/deployment.yaml
kubectl apply -f deploy/k8s/service.yaml
```

## Health Checks

Kubernetes:

```bash
kubectl -n hybridrag get pods
kubectl -n hybridrag get svc
kubectl -n hybridrag logs deploy/hybridrag-mcp --tail=200
```

Application validation:

1. Confirm service responds on health endpoint.
2. Run representative HybridRAG queries from your team test set.
3. Verify both vector and graph evidence are returned.
4. Confirm `X-Correlation-ID` header is present in all `/ask` responses.
5. Confirm guardrail blocks an obvious injection string (e.g. `"ignore previous instructions"`).

## Incident Response

### Severity Levels

1. Sev-1: Full outage, no query responses.
2. Sev-2: Partial degradation, high latency or retrieval failures.
3. Sev-3: Non-critical bug with workaround available.

### First 15 Minutes Checklist

1. Confirm blast radius (all users vs subset).
2. Check pod status and restart counts.
3. Inspect recent deployment and config changes.
4. Validate external dependencies (Databricks, Neo4j/Neptune, Anthropic).
5. Capture logs and timestamps for timeline.

### Common Failure Modes

1. Authentication or expired secrets:
   - Rotate secret in AWS Secrets Manager.
   - Restart deployment if env vars are loaded at startup.
2. Databricks retrieval failures:
   - Pipeline degrades gracefully to empty vector results with a `missing_evidence_warnings` entry.
   - Validate endpoint/index names and workspace permissions.
3. Graph backend connectivity issues:
   - Pipeline degrades to vector-only; graph warnings appear in the response.
   - Verify network ACL/security group/route rules.
4. LLM (Anthropic) failures:
   - API returns raw retrieved chunk text as fallback answer.
   - Check API key, quota, and provider status.
5. Kafka consumption failures:
   - Verify bootstrap servers, topic, SASL settings, and ACLs.
   - Check poison-pill events in logs (schema mismatch or invalid JSON).
6. Kafka Connect sink failures:
   - Check connector status, task errors, and DLQ topic growth.
   - Validate sink-specific classes and connector plugin installation.
7. Guardrail false positives (legitimate queries blocked at HTTP 400):
   - Inspect `X-Correlation-ID` in the response and find the corresponding log entry.
   - Adjust `_HARD_BLOCK_TERMS` in `llm/guardrails.py` if a pattern is too broad.
8. Rate limit rejections (HTTP 429):
   - Default limit is 60 requests/60 s per IP.
   - For multi-replica deployments, replace the in-process limiter with Redis-backed middleware.

## Rollback Procedure

Use rollout history to revert quickly:

```bash
kubectl -n hybridrag rollout history deployment/hybridrag-mcp
kubectl -n hybridrag rollout undo deployment/hybridrag-mcp
kubectl -n hybridrag rollout status deployment/hybridrag-mcp
```

Post-rollback checks:

1. Confirm pods become Ready.
2. Re-run smoke tests.
3. Announce mitigation and begin root cause analysis.

## Change Management

Before production deploy:

1. Ensure tests pass.
2. Confirm image tag immutability.
3. Review manifest diffs.
4. Verify secret references and environment values.

After deploy:

1. Record deployed version and timestamp.
2. Capture validation results.
3. Create follow-up tasks for any known risk.

## Observability Recommendations

1. Enable LangSmith tracing (`LANGSMITH_TRACING=true`) for end-to-end supervisor trace capture including `prompt_version`.
2. All log lines are structured JSON with `correlation_id`; aggregate and search them by `correlation_id` to trace a single request.
3. Expose `X-Correlation-ID` in your load balancer and client-side logs to correlate frontend and backend traces.
4. Track latency and error rate by retrieval path (vector vs graph) and by `cache_hit` status.
5. Alert on pod restarts, 5xx rates, 429 rate-limit surges, and guardrail block spikes.
6. Maintain dashboards for throughput, latency, retrieval recall, and composite eval score trends.

## Ownership

Suggested minimum ownership map:

1. Application on-call: MCP and LangGraph service.
2. Data platform on-call: Databricks jobs and indexes.
3. Infrastructure on-call: EKS networking, IAM/IRSA, ingress.

## Appendix: Useful Commands

Format code:

```bash
ruff format .
```

Run tests:

```bash
pytest -q
```

Show current workload state:

```bash
kubectl -n hybridrag get deploy,pods,svc
```

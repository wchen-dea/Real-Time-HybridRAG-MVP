# Cost Model

## Purpose

This is a directional cost model for planning and operational control, not a strict budget forecast.

## Primary cost drivers

1. EKS service sizing and replica count.
2. Databricks AI Search endpoint and index usage.
3. Embedding and model-serving endpoint utilization.
4. Anthropic token consumption for generation and quality gates.
5. Graph database compute and storage (Neo4j or Neptune).
6. Databricks SQL warehouse runtime.
7. Observability ingestion and retention.

## Cost control levers

1. Tag all resources for cost attribution and showback.
2. Cap vector top-k and graph traversal depth to reduce retrieval overhead.
3. Keep bootstrap/indexing jobs separate from online serving workloads.
4. Right-size or remove unused endpoints and idle capacity.
5. Add quality-gate metrics to prevent low-value token usage.

## Suggested monthly review checklist

1. Compare request volume, latency, and token usage trends.
2. Review Databricks endpoint utilization and index hit quality.
3. Verify graph store sizing and query profile changes.
4. Reconcile cost tags with service ownership in runbook.md.

## Related docs

1. docs/production_deployment_aws_eks.md
2. runbook.md

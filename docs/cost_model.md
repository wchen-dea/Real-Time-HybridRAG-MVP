# Cost Model

Directional cost drivers: EKS replica sizing, Databricks AI Search endpoints/indexes, embedding/model serving endpoints, Anthropic token usage, graph database compute/storage, SQL warehouse usage, and observability retention.

Controls: tag all resources, cap vector top-k and graph depth, keep bootstrap jobs separate from online serving, avoid unused endpoints, and add quality-gate metrics.

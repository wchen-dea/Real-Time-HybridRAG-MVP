# Production Deployment Architecture: AWS EKS + Databricks + Neo4j/Neptune

```text
Client / Copilot / Agent -> private ingress -> EKS service hybridrag-mcp -> LangGraph -> Databricks AI Search + SQL -> Neo4j/Neptune -> Anthropic Claude
```

Use private subnets, IRSA-backed service account, Secrets Manager for secrets, internal service exposure, and separate bootstrap jobs for AI Search indexing and graph population.

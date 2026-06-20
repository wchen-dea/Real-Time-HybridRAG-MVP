# Kafka Connect Sinks

This folder contains connector templates for sinking Flink-enriched topics into vector and graph destinations.

## One-Command Deployment

Render templates and register connectors:

```bash
make connectors-deploy
```

Render only:

```bash
make connectors-render
```

## Connector Templates

- [Vector sink template](templates/vector_sink_databricks_jdbc.tmpl.json)
- [Graph sink template](templates/graph_sink_neo4j.tmpl.json)

Rendered output directory:

- generated/

## Expected Topics

1. `hybridrag.enriched.vector` — chunk records including `embedding ARRAY<FLOAT>` pre-computed by Flink
2. `hybridrag.enriched.graph` — lineage relationship records

## Register connectors

```bash
python scripts/deploy_connectors.py --register
```

The script upserts connectors (create if missing, update if existing).

## Notes

1. Replace all placeholders in JSON files before deployment.
2. Ensure required connector plugins are installed on worker nodes.
3. Configure DLQ topics and alerting for sink failures.
4. For local bootstrap, start the stack with:

```bash
make streaming-up
make streaming-topics
```

Related docs:

- [Tech Stack](../../README.md#tech-stack)
- [Architecture](../../docs/architecture.md)
- [Runbook](../../docs/runbook.md)

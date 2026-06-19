# Kafka Connect Sinks

This folder contains connector templates for sinking Flink-enriched topics into vector and graph destinations.

## One-command deployment

Render templates and register connectors:

```bash
make connectors-deploy
```

Render only:

```bash
make connectors-render
```

## Connectors

1. templates/vector_sink_databricks_jdbc.tmpl.json
2. templates/graph_sink_neo4j.tmpl.json

Rendered output directory:

1. generated/

## Topics expected

1. hybridrag.enriched.vector
2. hybridrag.enriched.graph

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

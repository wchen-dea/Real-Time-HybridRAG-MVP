#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="deploy/docker/docker-compose.streaming.yml"
RAW_TOPIC="${KAFKA_RAW_TOPIC:-hybridrag.raw.events}"
VECTOR_TOPIC="${KAFKA_ENRICHED_VECTOR_TOPIC:-hybridrag.enriched.vector}"
GRAPH_TOPIC="${KAFKA_ENRICHED_GRAPH_TOPIC:-hybridrag.enriched.graph}"

for topic in "$RAW_TOPIC" "$VECTOR_TOPIC" "$GRAPH_TOPIC"; do
  docker compose -f "$COMPOSE_FILE" exec -T kafka \
    kafka-topics --create --if-not-exists \
    --bootstrap-server kafka:29092 \
    --topic "$topic" \
    --partitions 3 \
    --replication-factor 1
  echo "ensured topic: $topic"
done

# Kafka Connect internal topics
for topic in _connect-configs _connect-offsets _connect-status; do
  docker compose -f "$COMPOSE_FILE" exec -T kafka \
    kafka-topics --create --if-not-exists \
    --bootstrap-server kafka:29092 \
    --topic "$topic" \
    --partitions 1 \
    --replication-factor 1
  echo "ensured topic: $topic"
done

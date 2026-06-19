from __future__ import annotations

import json
import random
import signal
import time
import uuid
from typing import Any
from dataclasses import dataclass
from datetime import datetime, timezone

from confluent_kafka import Producer

from dataops_graphrag_mcp.common.logging import get_logger
from dataops_graphrag_mcp.common.settings import settings

logger = get_logger(__name__)

PIPELINES = ["kafka_to_delta", "lineage_to_catalog", "ops_events_to_gold"]
APPS = ["lineage-job", "ops-health-job", "catalog-sync-job"]
TOPICS = ["ops.lineage", "ops.events", "ops.monitoring"]
OWNER_TEAMS = ["data-platform", "data-eng", "streaming-ops"]
DASHBOARDS = ["Lineage Dashboard", "Kafka Ops", "Data Health"]
DOMAINS = ["operations", "streaming", "governance"]
SYSTEMS = ["kafka", "flink", "databricks"]


@dataclass
class ProducerRuntime:
    stop_requested: bool = False


def _producer_config() -> dict[str, str]:
    config: dict[str, str] = {
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "client.id": settings.kafka_producer_client_id,
        "security.protocol": settings.kafka_security_protocol,
    }
    if settings.kafka_sasl_username and settings.kafka_sasl_password:
        config["sasl.mechanisms"] = settings.kafka_sasl_mechanism
        config["sasl.username"] = settings.kafka_sasl_username
        config["sasl.password"] = settings.kafka_sasl_password
    return config


def _build_event(counter: int) -> dict[str, object]:
    pipeline = random.choice(PIPELINES)
    topic = random.choice(TOPICS)
    app = random.choice(APPS)
    team = random.choice(OWNER_TEAMS)
    doc_id = f"chunk-{counter % 5000:05d}"
    now = datetime.now(timezone.utc).isoformat()

    return {
        "event_id": str(uuid.uuid4()),
        "op": "upsert",
        "event_time": now,
        "pipeline": pipeline,
        "flink_application": app,
        "kafka_topic": topic,
        "schema_subject": f"{topic}-value",
        "delta_table": "ai_context.document_chunks",
        "snowflake_object": "ANALYTICS.DOCUMENT_CHUNKS",
        "dashboard": random.choice(DASHBOARDS),
        "owner_team": team,
        "chunk_id": doc_id,
        "chunk_text": (
            f"Streaming update {counter} for {pipeline}. "
            f"Lag={random.randint(5, 800)}ms throughput={random.randint(100, 2000)}rps"
        ),
        "title": f"{pipeline} status update",
        "source_name": "confluent_kafka_producer",
        "source_uri": f"kafka://{topic}/{doc_id}",
        "domain": random.choice(DOMAINS),
        "system_name": random.choice(SYSTEMS),
        "environment": settings.app_env,
    }


def run() -> None:
    runtime = ProducerRuntime()

    def _request_stop(_sig: int, _frame: object | None) -> None:
        runtime.stop_requested = True

    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)

    producer = Producer(_producer_config())

    def _delivery_report(err: Exception | None, msg: Any) -> None:
        if err is not None:
            logger.error("Delivery failed: %s", err)
            return
        try:
            logger.debug(
                "Delivered topic=%s partition=%s offset=%s",
                msg.topic(),
                msg.partition(),
                msg.offset(),
            )
        except Exception:
            logger.debug("Delivered message")

    logger.info("Producing changing events to topic=%s", settings.kafka_raw_topic)

    counter = 0
    try:
        while not runtime.stop_requested:
            event = _build_event(counter)
            payload = json.dumps(event).encode("utf-8")
            producer.produce(
                settings.kafka_raw_topic,
                value=payload,
                key=str(event["chunk_id"]),
                callback=_delivery_report,
            )
            producer.poll(0)
            counter += 1
            time.sleep(settings.kafka_produce_interval_seconds)
    finally:
        producer.flush(10)
        logger.info("Producer stopped after %s events", counter)


if __name__ == "__main__":
    run()

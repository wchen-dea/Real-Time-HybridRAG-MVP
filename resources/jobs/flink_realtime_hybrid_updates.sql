-- Flink SQL pipeline:
-- 1) consume changing events from raw Confluent Kafka topic
-- 2) enrich and format records
-- 3) publish to two layered topics for dedicated Kafka Connect sinks

CREATE TABLE source_events (
  event_id STRING,
  op STRING,
  event_time TIMESTAMP(3),
  pipeline STRING,
  flink_application STRING,
  kafka_topic STRING,
  schema_subject STRING,
  delta_table STRING,
  snowflake_object STRING,
  dashboard STRING,
  owner_team STRING,
  chunk_id STRING,
  chunk_text STRING,
  title STRING,
  source_name STRING,
  source_uri STRING,
  domain STRING,
  system_name STRING,
  environment STRING,
  WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'hybridrag.raw.events',
  'properties.bootstrap.servers' = 'broker-1:9092,broker-2:9092',
  'properties.group.id' = 'flink-hybridrag-transform',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json'
);

CREATE TABLE vector_updates (
  event_id STRING,
  op STRING,
  event_time STRING,
  chunk_id STRING,
  source_type STRING,
  source_name STRING,
  source_uri STRING,
  title STRING,
  chunk_text STRING,
  domain STRING,
  system_name STRING,
  environment STRING,
  owner_team STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'hybridrag.enriched.vector',
  'properties.bootstrap.servers' = 'broker-1:9092,broker-2:9092',
  'format' = 'json',
  'json.timestamp-format.standard' = 'ISO-8601'
);

CREATE TABLE graph_updates (
  event_id STRING,
  op STRING,
  event_time STRING,
  pipeline STRING,
  flink_application STRING,
  kafka_topic STRING,
  schema_subject STRING,
  delta_table STRING,
  snowflake_object STRING,
  dashboard STRING,
  owner_team STRING,
  environment STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'hybridrag.enriched.graph',
  'properties.bootstrap.servers' = 'broker-1:9092,broker-2:9092',
  'format' = 'json',
  'json.timestamp-format.standard' = 'ISO-8601'
);

INSERT INTO vector_updates
SELECT
  event_id,
  COALESCE(op, 'upsert') AS op,
  DATE_FORMAT(event_time, 'yyyy-MM-dd''T''HH:mm:ss.SSSXXX') AS event_time,
  chunk_id,
  'stream' AS source_type,
  COALESCE(source_name, 'flink_stream') AS source_name,
  source_uri,
  COALESCE(title, '') AS title,
  chunk_text,
  COALESCE(domain, '') AS domain,
  COALESCE(system_name, '') AS system_name,
  COALESCE(environment, 'dev') AS environment,
  COALESCE(owner_team, '') AS owner_team
FROM source_events;

INSERT INTO graph_updates
SELECT
  event_id,
  COALESCE(op, 'upsert') AS op,
  DATE_FORMAT(event_time, 'yyyy-MM-dd''T''HH:mm:ss.SSSXXX') AS event_time,
  pipeline,
  flink_application,
  kafka_topic,
  schema_subject,
  delta_table,
  snowflake_object,
  dashboard,
  owner_team,
  COALESCE(environment, 'dev') AS environment
FROM source_events;

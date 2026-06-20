CREATE TABLE IF NOT EXISTS ai_context.document_chunks (
  chunk_id STRING,
  source_type STRING,
  source_name STRING,
  source_uri STRING,
  title STRING,
  chunk_text STRING,
  embedding ARRAY<FLOAT>,  -- pre-computed by Flink embedding UDF; NULL when using Databricks Delta Sync auto-embedding
  domain STRING,
  system_name STRING,
  environment STRING,
  owner_team STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

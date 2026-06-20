from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = Field(default="dev", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    databricks_host: str = Field(default="", alias="DATABRICKS_HOST")
    databricks_token: str = Field(default="", alias="DATABRICKS_TOKEN")
    databricks_sql_warehouse_id: str = Field(
        default="", alias="DATABRICKS_SQL_WAREHOUSE_ID"
    )
    databricks_sql_http_path: str = Field(default="", alias="DATABRICKS_SQL_HTTP_PATH")
    vector_index_name: str = Field(
        default="ai_context.document_chunks_index", alias="VECTOR_INDEX_NAME"
    )
    vector_top_k: int = Field(default=8, alias="VECTOR_TOP_K")
    ai_search_endpoint_name: str = Field(
        default="hybridrag-ai-search-endpoint", alias="AI_SEARCH_ENDPOINT_NAME"
    )
    ai_search_source_table: str = Field(
        default="ai_context.document_chunks", alias="AI_SEARCH_SOURCE_TABLE"
    )
    ai_search_index_fullname: str = Field(
        default="ai_context.document_chunks_index", alias="AI_SEARCH_INDEX_FULLNAME"
    )
    ai_search_embedding_model_endpoint: str = Field(
        default="databricks-gte-large-en", alias="AI_SEARCH_EMBEDDING_MODEL_ENDPOINT"
    )
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")
    llm_provider: str = Field(default="anthropic", alias="LLM_PROVIDER")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-latest", alias="ANTHROPIC_MODEL"
    )
    anthropic_max_tokens: int = Field(default=2048, alias="ANTHROPIC_MAX_TOKENS")
    anthropic_temperature: float = Field(default=0.1, alias="ANTHROPIC_TEMPERATURE")
    langsmith_tracing: bool = Field(default=False, alias="LANGSMITH_TRACING")
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    langsmith_endpoint: str = Field(
        default="https://api.smith.langchain.com", alias="LANGSMITH_ENDPOINT"
    )
    langsmith_project: str = Field(
        default="real-time-hybridrag-mvp", alias="LANGSMITH_PROJECT"
    )
    langsmith_tags: str = Field(default="hybridrag,mvp", alias="LANGSMITH_TAGS")
    mcp_server_name: str = Field(
        default="dataops-graphrag-mcp", alias="MCP_SERVER_NAME"
    )
    mcp_server_host: str = Field(default="0.0.0.0", alias="MCP_SERVER_HOST")
    mcp_server_port: int = Field(default=8088, alias="MCP_SERVER_PORT")
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_raw_topic: str = Field(
        default="hybridrag.raw.events", alias="KAFKA_RAW_TOPIC"
    )
    kafka_enriched_vector_topic: str = Field(
        default="hybridrag.enriched.vector", alias="KAFKA_ENRICHED_VECTOR_TOPIC"
    )
    kafka_enriched_graph_topic: str = Field(
        default="hybridrag.enriched.graph", alias="KAFKA_ENRICHED_GRAPH_TOPIC"
    )
    kafka_security_protocol: str = Field(
        default="PLAINTEXT", alias="KAFKA_SECURITY_PROTOCOL"
    )
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_sasl_username: str = Field(default="", alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(default="", alias="KAFKA_SASL_PASSWORD")
    kafka_producer_client_id: str = Field(
        default="hybridrag-event-producer", alias="KAFKA_PRODUCER_CLIENT_ID"
    )
    kafka_produce_interval_seconds: float = Field(
        default=1.0, alias="KAFKA_PRODUCE_INTERVAL_SECONDS"
    )

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

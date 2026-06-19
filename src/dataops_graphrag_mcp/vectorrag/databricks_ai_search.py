from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from dataops_graphrag_mcp.common.settings import settings


@dataclass
class AISearchConfig:
    endpoint_name: str
    source_table_fullname: str
    index_fullname: str
    primary_key: str = "chunk_id"
    embedding_source_column: str = "chunk_text"
    embedding_model_endpoint_name: str = "databricks-gte-large-en"
    endpoint_type: str = "STANDARD"
    pipeline_type: str = "TRIGGERED"


class DatabricksAISearchVectorStore:
    def __init__(self, config: AISearchConfig):
        from databricks.ai_search.client import AISearchClient

        self.config = config
        self.client = AISearchClient()

    def ensure_endpoint(self) -> None:
        if not self.client.endpoint_exists(self.config.endpoint_name):
            self.client.create_endpoint(
                name=self.config.endpoint_name, endpoint_type=self.config.endpoint_type
            )
            self.client.wait_for_endpoint(self.config.endpoint_name)

    def ensure_delta_sync_index(self) -> None:
        self.ensure_endpoint()
        if not self.client.index_exists(self.config.index_fullname):
            self.client.create_delta_sync_index(
                endpoint_name=self.config.endpoint_name,
                source_table_name=self.config.source_table_fullname,
                index_name=self.config.index_fullname,
                pipeline_type=self.config.pipeline_type,
                primary_key=self.config.primary_key,
                embedding_source_column=self.config.embedding_source_column,
                embedding_model_endpoint_name=self.config.embedding_model_endpoint_name,
            )
        self.client.get_index(index_name=self.config.index_fullname).wait_until_ready()

    def sync(self) -> None:
        self.client.get_index(index_name=self.config.index_fullname).sync()

    def similarity_search(
        self,
        query_text: str,
        columns: list[str] | None = None,
        num_results: int | None = None,
        query_type: str = "hybrid",
        filters: dict[str, Any] | None = None,
    ) -> Any:
        index = self.client.get_index(index_name=self.config.index_fullname)
        return index.similarity_search(
            query_text=query_text,
            columns=columns
            or ["chunk_id", "title", "source_name", "source_uri", "chunk_text"],
            num_results=num_results or settings.vector_top_k,
            query_type=query_type,
            filters=filters,
        )

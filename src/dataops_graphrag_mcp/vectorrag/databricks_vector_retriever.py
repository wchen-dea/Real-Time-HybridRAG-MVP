from dataclasses import dataclass
from dataops_graphrag_mcp.common.settings import settings
from dataops_graphrag_mcp.vectorrag.databricks_ai_search import (
    AISearchConfig,
    DatabricksAISearchVectorStore,
)
from dataops_graphrag_mcp.vectorrag.vector_retriever import VectorSearchResult


@dataclass
class DatabricksVectorRetrieverConfig:
    endpoint_name: str
    source_table_fullname: str
    index_fullname: str
    embedding_model_endpoint_name: str = "databricks-gte-large-en"


class DatabricksVectorRetriever:
    def __init__(self, config: DatabricksVectorRetrieverConfig):
        self.store = DatabricksAISearchVectorStore(
            AISearchConfig(
                config.endpoint_name,
                config.source_table_fullname,
                config.index_fullname,
                embedding_model_endpoint_name=config.embedding_model_endpoint_name,
            )
        )

    def bootstrap(self) -> None:
        self.store.ensure_delta_sync_index()

    def search(
        self, query: str, filters: dict | None = None
    ) -> list[VectorSearchResult]:
        response = self.store.similarity_search(
            query_text=query,
            num_results=settings.vector_top_k,
            query_type="hybrid",
            filters=filters,
        )
        rows = (
            response.get("result", {}).get("data_array", [])
            if isinstance(response, dict)
            else []
        )
        return [
            VectorSearchResult(
                str(r[0]),
                str(r[1]),
                str(r[2]),
                r[3],
                str(r[4]),
                float(r[-1]) if isinstance(r[-1], (float, int)) else 0.0,
            )
            for r in rows
        ]

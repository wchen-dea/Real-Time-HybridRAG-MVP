from dataops_graphrag_mcp.common.settings import settings
from dataops_graphrag_mcp.vectorrag.databricks_vector_retriever import (
    DatabricksVectorRetriever,
    DatabricksVectorRetrieverConfig,
)


def main():
    retriever = DatabricksVectorRetriever(
        DatabricksVectorRetrieverConfig(
            settings.ai_search_endpoint_name,
            settings.ai_search_source_table,
            settings.ai_search_index_fullname,
            settings.ai_search_embedding_model_endpoint,
        )
    )
    retriever.bootstrap()
    print("Databricks AI Search endpoint/index bootstrap complete.")


if __name__ == "__main__":
    main()

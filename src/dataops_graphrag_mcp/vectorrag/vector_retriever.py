from dataclasses import dataclass


@dataclass
class VectorSearchResult:
    chunk_id: str
    title: str
    source_name: str
    source_uri: str | None
    chunk_text: str
    score: float


class VectorRetriever:
    def __init__(self, index_name: str, top_k: int = 8):
        self.index_name = index_name
        self.top_k = top_k

    def search(
        self, query: str, filters: dict | None = None
    ) -> list[VectorSearchResult]:
        return [
            VectorSearchResult(
                "sample-001",
                "Kafka/Flink Monitoring Runbook",
                "runbook",
                None,
                "Check Kafka lag, Flink backpressure, checkpoint health, and sink throughput.",
                0.91,
            )
        ]

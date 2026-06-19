from enum import Enum


class RetrievalMode(str, Enum):
    VECTOR = "vector"
    GRAPH = "graph"
    HYBRID = "hybrid"
    SQL = "sql"


class QueryRouter:
    GRAPH_TERMS = [
        "impact",
        "downstream",
        "upstream",
        "lineage",
        "dependency",
        "connected",
    ]
    VECTOR_TERMS = [
        "runbook",
        "documentation",
        "how to",
        "explain",
        "summarize",
        "similar incident",
        "rca",
    ]

    def route(self, query: str) -> RetrievalMode:
        q = query.lower()
        g = any(t in q for t in self.GRAPH_TERMS)
        v = any(t in q for t in self.VECTOR_TERMS)
        if g and v:
            return RetrievalMode.HYBRID
        if g:
            return RetrievalMode.GRAPH
        if v:
            return RetrievalMode.VECTOR
        return RetrievalMode.HYBRID

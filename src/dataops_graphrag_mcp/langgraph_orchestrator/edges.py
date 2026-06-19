def route_after_classification(state):
    mode = state.get("retrieval_mode", "hybrid")
    if mode == "vector":
        return "vector_retrieval"
    if mode == "graph":
        return "entity_extraction"
    if mode == "sql":
        return "databricks_sql"
    return "entity_extraction"


def route_after_entity_extraction(state):
    if state.get("retrieval_mode") == "graph":
        return "graph_retrieval"
    if state.get("retrieval_mode") == "hybrid":
        return "vector_retrieval"
    return "evidence_merge"


def route_after_vector_retrieval(state):
    return (
        "graph_retrieval"
        if state.get("retrieval_mode") == "hybrid"
        else "evidence_merge"
    )


def route_after_quality_gate(state):
    return "end"

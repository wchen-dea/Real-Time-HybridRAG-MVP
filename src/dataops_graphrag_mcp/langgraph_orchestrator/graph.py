from langgraph.graph import END, START, StateGraph
from dataops_graphrag_mcp.langgraph_orchestrator.state import DataOpsAgentState
from dataops_graphrag_mcp.langgraph_orchestrator.nodes import (
    classify_query_node,
    entity_extraction_node,
    vector_retrieval_node,
    graph_retrieval_node,
    databricks_sql_node,
    evidence_merge_node,
    answer_generation_node,
    quality_gate_node,
)
from dataops_graphrag_mcp.langgraph_orchestrator.edges import (
    route_after_classification,
    route_after_entity_extraction,
    route_after_vector_retrieval,
    route_after_quality_gate,
)


def build_dataops_langgraph():
    workflow = StateGraph(DataOpsAgentState)
    for name, fn in {
        "classify_query": classify_query_node,
        "entity_extraction": entity_extraction_node,
        "vector_retrieval": vector_retrieval_node,
        "graph_retrieval": graph_retrieval_node,
        "databricks_sql": databricks_sql_node,
        "evidence_merge": evidence_merge_node,
        "answer_generation": answer_generation_node,
        "quality_gate": quality_gate_node,
    }.items():
        workflow.add_node(name, fn)
    workflow.add_edge(START, "classify_query")
    workflow.add_conditional_edges(
        "classify_query",
        route_after_classification,
        {
            "vector_retrieval": "vector_retrieval",
            "entity_extraction": "entity_extraction",
            "databricks_sql": "databricks_sql",
        },
    )
    workflow.add_conditional_edges(
        "entity_extraction",
        route_after_entity_extraction,
        {
            "graph_retrieval": "graph_retrieval",
            "vector_retrieval": "vector_retrieval",
            "evidence_merge": "evidence_merge",
        },
    )
    workflow.add_conditional_edges(
        "vector_retrieval",
        route_after_vector_retrieval,
        {"graph_retrieval": "graph_retrieval", "evidence_merge": "evidence_merge"},
    )
    workflow.add_edge("graph_retrieval", "databricks_sql")
    workflow.add_edge("databricks_sql", "evidence_merge")
    workflow.add_edge("evidence_merge", "answer_generation")
    workflow.add_edge("answer_generation", "quality_gate")
    workflow.add_conditional_edges(
        "quality_gate", route_after_quality_gate, {"end": END}
    )
    return workflow.compile()

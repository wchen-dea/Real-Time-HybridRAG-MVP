import json
from dataops_graphrag_mcp.common.settings import settings
from dataops_graphrag_mcp.hybrid.query_router import QueryRouter
from dataops_graphrag_mcp.vectorrag.vector_retriever import VectorRetriever
from dataops_graphrag_mcp.graphrag.graph_retriever import GraphRetriever
from dataops_graphrag_mcp.hybrid.evidence_merger import EvidenceMerger
from dataops_graphrag_mcp.llm.provider import get_chat_model
from dataops_graphrag_mcp.llm.prompts import (
    ENTITY_EXTRACTION_PROMPT,
    ANSWER_GENERATION_PROMPT,
)


def classify_query_node(state):
    return {"retrieval_mode": QueryRouter().route(state["question"]).value}


def entity_extraction_node(state):
    if not settings.anthropic_api_key:
        return {
            "extracted_entities": {"primary_entity": None},
            "target_entity_name": None,
        }
    content = (
        get_chat_model()
        .invoke(ENTITY_EXTRACTION_PROMPT.format(question=state["question"]))
        .content
    )
    try:
        extracted = json.loads(content)
    except json.JSONDecodeError:
        extracted = {"primary_entity": None, "parse_error": content}
    return {
        "extracted_entities": extracted,
        "target_entity_name": extracted.get("primary_entity"),
    }


def vector_retrieval_node(state):
    return {
        "vector_results": [
            r.__dict__
            for r in VectorRetriever(
                settings.vector_index_name, settings.vector_top_k
            ).search(state["question"])
        ]
    }


def graph_retrieval_node(state):
    entity = state.get("target_entity_name")
    if not entity:
        return {
            "graph_results": [],
            "missing_evidence_warnings": ["No graph entity extracted."],
        }
    retriever = GraphRetriever(
        settings.neo4j_uri,
        settings.neo4j_user,
        settings.neo4j_password,
        settings.neo4j_database,
    )
    try:
        triples = retriever.get_downstream_impact(entity)
    finally:
        retriever.close()
    return {"graph_results": [t.__dict__ for t in triples]}


def databricks_sql_node(state):
    return {"sql_results": []}


def evidence_merge_node(state):
    vr = [type("VectorResult", (), r) for r in state.get("vector_results", [])]
    gr = [type("GraphResult", (), r) for r in state.get("graph_results", [])]
    evidence, graph_path = EvidenceMerger().merge_vector_and_graph(vr, gr)
    return {"evidence": evidence, "graph_path": graph_path}


def answer_generation_node(state):
    evidence = [
        e.model_dump() if hasattr(e, "model_dump") else e
        for e in state.get("evidence", [])
    ]
    graph_path = [
        g.model_dump() if hasattr(g, "model_dump") else g
        for g in state.get("graph_path", [])
    ]
    if settings.anthropic_api_key:
        prompt = ANSWER_GENERATION_PROMPT.format(
            question=state["question"],
            vector_evidence=json.dumps(evidence),
            graph_path=json.dumps(graph_path),
            sql_results=json.dumps(state.get("sql_results", [])),
        )
        answer = get_chat_model().invoke(prompt).content
    else:
        answer = f"MVP response: found {len(evidence)} evidence items and {len(graph_path)} graph relationships."
    return {
        "final_answer": answer,
        "confidence": 0.75 if evidence or graph_path else 0.35,
        "recommended_next_actions": [
            "Validate graph path.",
            "Check latest operational metrics.",
        ],
    }


def quality_gate_node(state):
    return {
        "quality_gate_passed": bool(state.get("evidence") or state.get("graph_path"))
    }

from dataops_graphrag_mcp.hybrid.response_contract import EvidenceItem, GraphPathItem


class EvidenceMerger:
    def merge_vector_and_graph(self, vector_results: list, graph_results: list):
        evidence = [
            EvidenceItem(
                source_type="vector_chunk",
                source_name=r.source_name,
                source_uri=r.source_uri,
                excerpt=r.chunk_text,
                confidence=r.score,
            )
            for r in vector_results
        ]
        graph_path = [
            GraphPathItem(
                source_node=g.source_node,
                relationship=g.relationship,
                target_node=g.target_node,
            )
            for g in graph_results
        ]
        return evidence, graph_path

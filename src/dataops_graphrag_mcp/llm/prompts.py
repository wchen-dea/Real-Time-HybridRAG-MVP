ENTITY_EXTRACTION_PROMPT = """
Extract operational entities from the user question. Return JSON only:
{"primary_entity": null, "pipelines": [], "kafka_topics": [], "flink_applications": [], "delta_tables": [], "environment": null}
Question: {question}
"""
ANSWER_GENERATION_PROMPT = """
Use only the provided evidence, graph paths, and SQL results. Do not invent facts.
Question: {question}
Vector evidence: {vector_evidence}
Graph path: {graph_path}
SQL results: {sql_results}
Return: Summary, Evidence, Graph Path, Recommended Next Actions, Confidence, Missing Evidence Warnings.
"""
QUALITY_GATE_PROMPT = """
Return JSON only: {"quality_gate_passed": true, "issues": [], "confidence": 0.0}
Question: {question}
Answer: {answer}
Evidence: {evidence}
Graph path: {graph_path}
"""

from dataclasses import dataclass
from neo4j import GraphDatabase


@dataclass
class GraphTriple:
    source_node: str
    relationship: str
    target_node: str


class GraphRetriever:
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def get_downstream_impact(
        self, entity_name: str, max_depth: int = 5
    ) -> list[GraphTriple]:
        query = """MATCH path = (n {name: $entity_name})-[*1..5]->(m) UNWIND relationships(path) AS r RETURN startNode(r).name AS source_node, type(r) AS relationship, endNode(r).name AS target_node LIMIT 100"""
        triples = []
        with self.driver.session(database=self.database) as session:
            for row in session.run(query, entity_name=entity_name, max_depth=max_depth):
                triples.append(
                    GraphTriple(
                        row["source_node"], row["relationship"], row["target_node"]
                    )
                )
        return triples

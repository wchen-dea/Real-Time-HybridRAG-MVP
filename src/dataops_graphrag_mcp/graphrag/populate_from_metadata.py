from __future__ import annotations
import csv
from pathlib import Path
from typing import Iterable
from neo4j import GraphDatabase
from dataops_graphrag_mcp.common.settings import settings

CONSTRAINTS = [
    "CREATE CONSTRAINT pipeline_name IF NOT EXISTS FOR (n:Pipeline) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT kafka_topic_name IF NOT EXISTS FOR (n:KafkaTopic) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT flink_application_name IF NOT EXISTS FOR (n:FlinkApplication) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT delta_table_name IF NOT EXISTS FOR (n:DeltaTable) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT snowflake_object_name IF NOT EXISTS FOR (n:SnowflakeObject) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT dashboard_name IF NOT EXISTS FOR (n:Dashboard) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT owner_team_name IF NOT EXISTS FOR (n:OwnerTeam) REQUIRE n.name IS UNIQUE",
]
UPSERT_QUERY = """
MERGE (p:Pipeline {name: $pipeline}) SET p.environment = $environment
MERGE (app:FlinkApplication {name: $flink_application}) SET app.environment = $environment
MERGE (topic:KafkaTopic {name: $kafka_topic}) SET topic.environment = $environment
MERGE (schema:SchemaSubject {name: $schema_subject}) SET schema.environment = $environment
MERGE (dt:DeltaTable {name: $delta_table}) SET dt.environment = $environment
MERGE (sf:SnowflakeObject {name: $snowflake_object}) SET sf.environment = $environment
MERGE (dash:Dashboard {name: $dashboard}) SET dash.environment = $environment
MERGE (team:OwnerTeam {name: $owner_team})
MERGE (team)-[:OWNS]->(p)
MERGE (p)-[:RUNS_AS]->(app)
MERGE (app)-[:CONSUMES_FROM]->(topic)
MERGE (topic)-[:USES_SCHEMA]->(schema)
MERGE (app)-[:PRODUCES]->(dt)
MERGE (dt)-[:EXPORTED_TO]->(sf)
MERGE (dash)-[:READS_FROM]->(sf)
"""


class MetadataGraphPopulator:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def close(self):
        self.driver.close()

    def apply_constraints(self):
        with self.driver.session(database=settings.neo4j_database) as session:
            for s in CONSTRAINTS:
                session.run(s)

    def upsert_rows(self, rows: Iterable[dict]) -> int:
        count = 0
        with self.driver.session(database=settings.neo4j_database) as session:
            for row in rows:
                session.run(UPSERT_QUERY, **row)
                count += 1
        return count


def load_csv(path: str | Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    rows = load_csv(Path("data/sample/kafka_flink_lineage.csv"))
    populator = MetadataGraphPopulator()
    try:
        populator.apply_constraints()
        count = populator.upsert_rows(rows)
    finally:
        populator.close()
    print(f"Loaded {count} lineage rows into Neo4j.")


if __name__ == "__main__":
    main()

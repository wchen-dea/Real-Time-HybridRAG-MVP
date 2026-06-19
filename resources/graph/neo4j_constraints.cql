CREATE CONSTRAINT pipeline_name IF NOT EXISTS FOR (n:Pipeline) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT kafka_topic_name IF NOT EXISTS FOR (n:KafkaTopic) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT flink_application_name IF NOT EXISTS FOR (n:FlinkApplication) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT delta_table_name IF NOT EXISTS FOR (n:DeltaTable) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT snowflake_object_name IF NOT EXISTS FOR (n:SnowflakeObject) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT dashboard_name IF NOT EXISTS FOR (n:Dashboard) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT owner_team_name IF NOT EXISTS FOR (n:OwnerTeam) REQUIRE n.name IS UNIQUE;

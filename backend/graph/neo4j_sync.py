"""Optional: pushes the same graph built in graph/build.py to a live Neo4j
AuraDB instance, using the Cypher schema CLAUDE.md specifies:

  (:Spec)-[:REQUIRES]->(:Equipment)-[:SUBMITTED_BY]->(:Vendor)
  -[:DELIVERS]->(:Shipment)-[:BLOCKS]->(:Task)-[:PRECEDES]->(:Task)...

No-ops with a clear message if NEO4J_URI isn't configured (see
app/core/config.py) -- this dev environment has no live AuraDB credentials,
so graph/build.py + precompute.py (NetworkX + JSON) are the actual demo
path. Run this once real credentials exist to mirror the same graph into a
queryable Cypher database for the "real deployment" story.
"""

import sys

from app.core.config import get_settings
from graph.build import build_graph


def sync() -> None:
    settings = get_settings()
    if not settings.neo4j_uri:
        print(
            "NEO4J_URI not configured -- skipping live sync. "
            "graph/build.py + data/graph.json are the demo path.",
            file=sys.stderr,
        )
        return

    from neo4j import GraphDatabase

    graph = build_graph()
    driver = GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        for node_id, data in graph.nodes(data=True):
            label = data["node_type"].capitalize()
            session.run(
                f"CREATE (n:{label} {{node_id: $node_id, label: $label_text}})",
                node_id=node_id,
                label_text=data["label"],
            )
        for u, v, data in graph.edges(data=True):
            relation = data["relation"]
            session.run(
                "MATCH (a {node_id: $u}), (b {node_id: $v}) "
                f"CREATE (a)-[:{relation}]->(b)",
                u=u,
                v=v,
            )
    driver.close()
    print(
        f"Synced {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges to "
        f"{settings.neo4j_uri}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    sync()

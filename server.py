"""iBKH MCP server: four curated biomedical cypher tools plus ad-hoc schema/read/write."""

from __future__ import annotations

import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from neo4j import Driver, GraphDatabase
from neo4j.exceptions import ClientError, Neo4jError

log = logging.getLogger("ibkh-mcp")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))


def _build_driver() -> Driver:
    return GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )


DB = os.environ.get("NEO4J_DATABASE", "neo4j")
ALLOW_WRITES = os.environ.get("IBKH_ALLOW_WRITES", "false").lower() == "true"

driver = _build_driver()
mcp = FastMCP("ibkh")


def _records(result) -> list[dict[str, Any]]:
    return [r.data() for r in result]


# --------------------------- Curated tools ---------------------------


@mcp.tool()
def find_shared_genes(disease_a: str, disease_b: str, limit: int = 200) -> list[dict[str, Any]]:
    """Find genes ASSOCIATED_WITH both diseases (case-insensitive partial name match).

    Use for "what genes do disease X and disease Y share?" questions.
    Returns rows of {disease_a, disease_b, gene}.

    Cypher template executed (verbatim):
        MATCH (d1:Disease)-[:ASSOCIATED_WITH]->(g:Gene)<-[:ASSOCIATED_WITH]-(d2:Disease)
        WHERE toLower(d1.name) CONTAINS toLower($disease_a)
          AND toLower(d2.name) CONTAINS toLower($disease_b)
          AND elementId(d1) <> elementId(d2)
        RETURN DISTINCT d1.name AS disease_a, d2.name AS disease_b, g.symbol AS gene
        ORDER BY gene
        LIMIT $limit
    """
    cypher = """
    MATCH (d1:Disease)-[:ASSOCIATED_WITH]->(g:Gene)<-[:ASSOCIATED_WITH]-(d2:Disease)
    WHERE toLower(d1.name) CONTAINS toLower($disease_a)
      AND toLower(d2.name) CONTAINS toLower($disease_b)
      AND elementId(d1) <> elementId(d2)
    RETURN DISTINCT d1.name AS disease_a, d2.name AS disease_b, g.symbol AS gene
    ORDER BY gene
    LIMIT $limit
    """
    with driver.session(database=DB) as s:
        return s.execute_read(
            lambda tx: _records(tx.run(cypher, disease_a=disease_a, disease_b=disease_b, limit=limit))
        )


@mcp.tool()
def find_shared_genes_impacted_by_drug(
    disease_a: str,
    disease_b: str,
    drug_prefix: str,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Find genes shared between two diseases that a specific drug also touches.

    `drug_prefix` is matched case-insensitively against the start of Drug.name
    (e.g. "hydroxychloro" finds Hydroxychloroquine).
    Returns rows of {disease_a, disease_b, drug, gene, drug_gene_relation}.

    Cypher template executed (verbatim):
        MATCH (d1:Disease)-[:ASSOCIATED_WITH]->(g:Gene)<-[:ASSOCIATED_WITH]-(d2:Disease),
              (d1)<-[:TREATS]-(dr:Drug)-[r]-(g)
        WHERE toLower(d1.name) CONTAINS toLower($disease_a)
          AND toLower(d2.name) CONTAINS toLower($disease_b)
          AND toLower(dr.name) STARTS WITH toLower($drug_prefix)
          AND elementId(d1) <> elementId(d2)
        RETURN DISTINCT d1.name AS disease_a, d2.name AS disease_b,
               dr.name AS drug, g.symbol AS gene, type(r) AS drug_gene_relation
        ORDER BY drug, gene
        LIMIT $limit
    """
    cypher = """
    MATCH (d1:Disease)-[:ASSOCIATED_WITH]->(g:Gene)<-[:ASSOCIATED_WITH]-(d2:Disease),
          (d1)<-[:TREATS]-(dr:Drug)-[r]-(g)
    WHERE toLower(d1.name) CONTAINS toLower($disease_a)
      AND toLower(d2.name) CONTAINS toLower($disease_b)
      AND toLower(dr.name) STARTS WITH toLower($drug_prefix)
      AND elementId(d1) <> elementId(d2)
    RETURN DISTINCT d1.name AS disease_a, d2.name AS disease_b,
           dr.name AS drug, g.symbol AS gene, type(r) AS drug_gene_relation
    ORDER BY drug, gene
    LIMIT $limit
    """
    with driver.session(database=DB) as s:
        return s.execute_read(
            lambda tx: _records(
                tx.run(
                    cypher,
                    disease_a=disease_a,
                    disease_b=disease_b,
                    drug_prefix=drug_prefix,
                    limit=limit,
                )
            )
        )


@mcp.tool()
def find_alternative_drugs(disease: str, avoid_disease: str, limit: int = 100) -> list[dict[str, Any]]:
    """Drugs that TREAT `disease` and are NOT linked (via any out-edge) to genes
    ASSOCIATED_WITH `avoid_disease`.

    Use for "alternatives to drug X for condition A that don't impact condition B" questions.
    Both names are case-insensitive partial matches.

    Cypher template executed (verbatim):
        MATCH (dr:Drug)-[:TREATS]->(d:Disease)
        WHERE toLower(d.name) CONTAINS toLower($disease)
          AND NOT EXISTS {
            MATCH (dr)-[]->(g:Gene)<-[:ASSOCIATED_WITH]-(d2:Disease)
            WHERE toLower(d2.name) CONTAINS toLower($avoid_disease)
          }
        RETURN DISTINCT dr.name AS drug
        ORDER BY drug
        LIMIT $limit
    """
    cypher = """
    MATCH (dr:Drug)-[:TREATS]->(d:Disease)
    WHERE toLower(d.name) CONTAINS toLower($disease)
      AND NOT EXISTS {
        MATCH (dr)-[]->(g:Gene)<-[:ASSOCIATED_WITH]-(d2:Disease)
        WHERE toLower(d2.name) CONTAINS toLower($avoid_disease)
      }
    RETURN DISTINCT dr.name AS drug
    ORDER BY drug
    LIMIT $limit
    """
    with driver.session(database=DB) as s:
        return s.execute_read(
            lambda tx: _records(
                tx.run(cypher, disease=disease, avoid_disease=avoid_disease, limit=limit)
            )
        )


@mcp.tool()
def find_regulatory_gene_paths(
    disease_a: str,
    disease_b: str,
    max_hops: int = 2,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Find gene paths between two diseases via 0–`max_hops` SAME_PROTEIN_OR_COMPLEX edges.

    Surfaces indirect gene–gene regulation between diseases (Jeff's variable-hop pattern).
    `max_hops` is bounded to 0–5. Returns {disease_a, disease_b, source_gene, target_gene, hops}.

    Cypher template executed (verbatim, with `<MAX_HOPS>` substituted at call time because
    Cypher quantified path patterns require a literal upper bound):
        MATCH p=(d1:Disease)-[:ASSOCIATED_WITH]->(g1:Gene)
              ((:Gene)<-[:SAME_PROTEIN_OR_COMPLEX]-(:Gene)){0,<MAX_HOPS>}
              (g2:Gene)<-[:ASSOCIATED_WITH]-(d2:Disease)
        WHERE toLower(d1.name) CONTAINS toLower($disease_a)
          AND toLower(d2.name) CONTAINS toLower($disease_b)
        RETURN DISTINCT d1.name AS disease_a, d2.name AS disease_b,
               g1.symbol AS source_gene, g2.symbol AS target_gene, length(p) AS hops
        ORDER BY hops, source_gene
        LIMIT $limit
    """
    if not isinstance(max_hops, int) or not 0 <= max_hops <= 5:
        raise ValueError("max_hops must be an int in [0, 5]")
    # max_hops is interpolated as a literal because Cypher quantified path patterns
    # require literal bounds. Value is validated above to prevent injection.
    cypher = f"""
    MATCH p=(d1:Disease)-[:ASSOCIATED_WITH]->(g1:Gene)
          ((:Gene)<-[:SAME_PROTEIN_OR_COMPLEX]-(:Gene)){{0,{max_hops}}}
          (g2:Gene)<-[:ASSOCIATED_WITH]-(d2:Disease)
    WHERE toLower(d1.name) CONTAINS toLower($disease_a)
      AND toLower(d2.name) CONTAINS toLower($disease_b)
    RETURN DISTINCT d1.name AS disease_a, d2.name AS disease_b,
           g1.symbol AS source_gene, g2.symbol AS target_gene, length(p) AS hops
    ORDER BY hops, source_gene
    LIMIT $limit
    """
    with driver.session(database=DB) as s:
        return s.execute_read(
            lambda tx: _records(
                tx.run(cypher, disease_a=disease_a, disease_b=disease_b, limit=limit)
            )
        )


# --------------------------- Ad-hoc tools ---------------------------


_SCHEMA_APOC = "CALL apoc.meta.schema() YIELD value RETURN value"

_SCHEMA_FALLBACK = """
CALL { CALL db.labels() YIELD label RETURN collect(label) AS labels }
CALL { CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS relationship_types }
CALL { CALL db.propertyKeys() YIELD propertyKey RETURN collect(propertyKey) AS property_keys }
RETURN labels, relationship_types, property_keys
"""


@mcp.tool()
def get_neo4j_schema() -> dict[str, Any]:
    """Return iBKH graph schema (labels, relationship types, property keys).

    Call before composing ad-hoc cypher with `read_neo4j_cypher` so you reference real
    labels and relationship types. Tries APOC first, falls back to plain procedures.
    """
    with driver.session(database=DB) as s:
        try:
            row = s.execute_read(lambda tx: tx.run(_SCHEMA_APOC).single())
            return {"source": "apoc.meta.schema", "schema": row["value"]}
        except (ClientError, Neo4jError) as e:
            log.info("APOC unavailable (%s); using fallback schema introspection.", e.code if hasattr(e, "code") else e)
            row = s.execute_read(lambda tx: tx.run(_SCHEMA_FALLBACK).single())
            return {
                "source": "db.labels/db.relationshipTypes/db.propertyKeys",
                "labels": row["labels"],
                "relationship_types": row["relationship_types"],
                "property_keys": row["property_keys"],
            }


@mcp.tool()
def read_neo4j_cypher(query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Run a read-only Cypher query against iBKH. Writes are rejected by the read transaction.

    Always pass values via `params` rather than concatenating into the query string.
    Example: query="MATCH (d:Disease) WHERE d.name CONTAINS $name RETURN d.name LIMIT 5",
             params={"name": "lupus"}.
    """
    params = params or {}
    with driver.session(database=DB) as s:
        return s.execute_read(lambda tx: _records(tx.run(query, **params)))


@mcp.tool()
def write_neo4j_cypher(query: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run a write Cypher query. Disabled unless `IBKH_ALLOW_WRITES=true` in the server env.

    Returns transaction counters (nodes/relationships/properties created or deleted).
    """
    if not ALLOW_WRITES:
        raise PermissionError(
            "Writes are disabled. Restart this MCP server with IBKH_ALLOW_WRITES=true to enable."
        )
    params = params or {}
    with driver.session(database=DB) as s:
        summary = s.execute_write(lambda tx: tx.run(query, **params).consume())
        c = summary.counters
        return {
            "nodes_created": c.nodes_created,
            "nodes_deleted": c.nodes_deleted,
            "relationships_created": c.relationships_created,
            "relationships_deleted": c.relationships_deleted,
            "properties_set": c.properties_set,
            "labels_added": c.labels_added,
            "labels_removed": c.labels_removed,
            "indexes_added": c.indexes_added,
            "indexes_removed": c.indexes_removed,
            "constraints_added": c.constraints_added,
            "constraints_removed": c.constraints_removed,
        }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

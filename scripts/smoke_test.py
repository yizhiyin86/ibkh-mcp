"""Standalone smoke test — verifies driver connection, schema introspection, and each curated query."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import server  # noqa: E402


def show(name, rows):
    print(f"\n=== {name} ({len(rows)} rows) ===")
    for r in rows[:5]:
        print(json.dumps(r, default=str))
    if len(rows) > 5:
        print(f"... +{len(rows) - 5} more")


def main() -> int:
    # 1. driver / connectivity
    server.driver.verify_connectivity()
    print("OK: driver connected")

    # 2. schema
    schema = server.get_neo4j_schema()
    print(f"OK: schema source = {schema['source']}")
    if "labels" in schema:
        print(f"   labels ({len(schema['labels'])}): {schema['labels'][:10]}")
        print(f"   rels ({len(schema['relationship_types'])}): {schema['relationship_types'][:10]}")
    elif "schema" in schema:
        print(f"   apoc keys: {list(schema['schema'].keys())[:10]}")

    # 3. curated tools — small limits to keep output tight
    show("find_shared_genes(lupus, macular degen)",
         server.find_shared_genes("lupus", "macular degen", limit=10))

    show("find_shared_genes_impacted_by_drug(lupus, macular degen, hydroxychloro)",
         server.find_shared_genes_impacted_by_drug("lupus", "macular degen", "hydroxychloro", limit=10))

    show("find_alternative_drugs(lupus, macular degen)",
         server.find_alternative_drugs("lupus", "macular degen", limit=10))

    show("find_regulatory_gene_paths(lupus, macular degen, max_hops=2)",
         server.find_regulatory_gene_paths("lupus", "macular degen", max_hops=2, limit=10))

    # 4. ad-hoc read passes through
    show("read_neo4j_cypher disease sample",
         server.read_neo4j_cypher(
             "MATCH (d:Disease) WHERE toLower(d.name) CONTAINS $n RETURN d.name AS name LIMIT 5",
             {"n": "lupus"},
         ))

    return 0


if __name__ == "__main__":
    sys.exit(main())

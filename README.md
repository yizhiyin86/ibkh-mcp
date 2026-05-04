# iBKH MCP

A Model Context Protocol server that lets Claude Desktop answer biomedical questions against the
iBKH (integrated Biomedical Knowledge Hub) Neo4j graph. Ships four curated Cypher tools for the
demo questions and three ad-hoc tools (`get_neo4j_schema`, `read_neo4j_cypher`,
`write_neo4j_cypher`) for everything else.

## Prerequisites

- macOS with [Claude Desktop](https://claude.ai/download) installed
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (`brew install uv`)
- iBKH Neo4j connection details (URI + your own username/password) — **request from the repo owner**, do not share

## Setup

```bash
git clone <this-repo-url> ibkh_mcp
cd ibkh_mcp
uv sync
```

Verify connectivity (substitute your creds):

```bash
NEO4J_URI="neo4j+ssc://<host>:<port>" \
NEO4J_USERNAME="<you>" NEO4J_PASSWORD="<you>" \
NEO4J_DATABASE="ibkh" \
uv run python scripts/smoke_test.py
```

Wire into Claude Desktop. Open
`~/Library/Application Support/Claude/claude_desktop_config.json` (create it if missing) and merge
the `ibkh` block from [`claude_desktop_config.example.json`](claude_desktop_config.example.json).
Substitute:

- `<UV_PATH>` → output of `which uv` (commonly `/opt/homebrew/bin/uv` on Apple Silicon,
  `/usr/local/bin/uv` on Intel). Claude Desktop does **not** inherit your shell PATH, so the
  absolute path is required.
- `<ABS_PATH_TO_REPO>` → absolute path to your clone (no `~` expansion).
- `<your-username>` / `<your-password>` → your iBKH creds.

Fully quit Claude Desktop (Cmd+Q — closing the window keeps it running) and reopen. You should
see seven tools under the `ibkh` server.

## Sample questions

- *What genes do lupus and macular degeneration share?* → `find_shared_genes`
- *Of those, which does hydroxychloroquine touch?* → `find_shared_genes_impacted_by_drug`
- *What lupus drugs avoid the macular-degeneration gene network?* → `find_alternative_drugs`
- *Find lupus genes that regulate macular-degeneration genes within 2 hops* →
  `find_regulatory_gene_paths`
- *How many drugs treat lupus in total?* → falls through to `read_neo4j_cypher` after
  `get_neo4j_schema`

## Tools

| Tool | Purpose |
|---|---|
| `find_shared_genes(disease_a, disease_b)` | Genes ASSOCIATED_WITH both diseases |
| `find_shared_genes_impacted_by_drug(disease_a, disease_b, drug_prefix)` | Shared genes that a named drug also touches |
| `find_alternative_drugs(disease, avoid_disease)` | Drugs treating X with no edges into Y's gene network |
| `find_regulatory_gene_paths(disease_a, disease_b, max_hops=2)` | Variable-hop SAME_PROTEIN_OR_COMPLEX gene paths |
| `get_neo4j_schema()` | Labels, relationship types, property keys (uses APOC if available) |
| `read_neo4j_cypher(query, params)` | Ad-hoc read transaction; writes are rejected |
| `write_neo4j_cypher(query, params)` | Ad-hoc write; gated on `IBKH_ALLOW_WRITES=true` |

## Notes

- The iBKH server uses a self-signed TLS cert, so the URI scheme must be `neo4j+ssc://`, not
  `neo4j+s://`.
- In iBKH, `Gene.symbol` is the human-readable identifier (HGNC symbol like `C2`, `VEGFA`).
  Disease and Drug nodes use `name`. The curated tools already wire this up; for ad-hoc Cypher,
  point Claude at this when needed.
- Writes are disabled by default. To enable, set `"IBKH_ALLOW_WRITES": "true"` in the Claude
  Desktop config and restart.

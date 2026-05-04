# iBKH demo — executive script (~6 min)

A live walkthrough of the iBKH MCP from inside Claude Desktop. Five questions, real biomedical
answers, with one pivot beat to address the inevitable "why a graph database?" question.

## Background (Jeff's framing)

SLE patients commonly receive hydroxychloroquine (Plaquenil) from rheumatologists. For women of
European descent there's a known ~20% adverse-event rate with macular degeneration, leading to
follow-up with a retinal specialist. The genetic links are now visible — and rheumatologists could
choose alternatives for at-risk patients before prescribing.

---

## Open *(~30 sec)*

> "SLE patients commonly get hydroxychloroquine — Plaquenil — from rheumatologists. It's
> effective, but for women of European descent there's a known ~20% risk of macular degeneration,
> so they end up bouncing to a retinal specialist. Until recently we couldn't see the genetic
> basis for that risk. Today, with the iBKH knowledge graph wired into Claude, a rheumatologist
> can answer that question before prescribing. **Five questions, all answered live. I'll explain
> along the way why this is built on a graph — and why it matters.**"

## 1. Confirm the genetic overlap *(~45 sec)*

**Type:** `What genes do lupus and macular degeneration share?`

**Punchline:** 8 shared genes. Four of them — **C2, C3, CFB, SERPING1** — are the complement
cascade, the molecular driver of both diseases. The biology is real.

## 2. Find the drug's footprint *(~45 sec)*

**Type:** `Of those, which does hydroxychloroquine touch?`

**Punchline:** **CCL2** — via `INTERACTION` and `UP_REGULATES`. There's the mechanistic bridge
from drug to retinal risk.

## 3. Surface safer alternatives *(~45 sec)*

**Type:** `What lupus drugs avoid the macular-degeneration gene network?`

**Punchline:** Hundreds of candidates out of **3,845** lupus drugs in iBKH. The rheumatologist now
has a filtered shortlist instead of a textbook.

---

## Pivot — *why this is on a graph* *(~45 sec)*

> "Pause for one second. You might be wondering — couldn't we do this in Postgres with regular
> tables and JOINs? Two reasons we didn't.
>
> **First, the next question is impossible to write cleanly in SQL.** It asks for genes connecting
> two diseases through one or two protein-complex hops — variable depth. In our graph language
> that's *one line*. In SQL it's three separate queries glued together, and you rewrite them every
> time you want to go deeper. Watch.
>
> **Second, iBKH grows by adding new connection types** — pathways, trials, side effects. In a
> graph that's a one-line update. In a relational schema it's a migration with foreign keys and
> re-indexing. Speed of biology requires speed of schema."

## 4. Go deeper into biology *(~45 sec)*

**Type:** `Find lupus genes that regulate macular-degeneration genes within 2 hops.`

**Punchline:** **10 lupus genes** connect to **10 AMD genes** through protein-complex
relationships. Indirect mechanistic biology — the kind of finding that takes weeks of literature
review. **That query is what graph buys us.**

## 5. Show flexibility *(~30 sec)*

**Type:** `How many drugs treat lupus in total?`

**Punchline:** **3,845.** Anything off-script — Claude reads the iBKH schema and writes its own
query on the fly. The clinician writes the question; Claude writes the code.

---

## Close *(~30 sec)*

> "Same workflow, any disease pair, any drug. Adding a new clinical question is about ten lines of
> code. Graph for relationship discovery; warehouse for analytics — both, not either-or. The whole
> demo runs from inside Claude Desktop, and the repo is one `git clone` away for any teammate."

---

## Anticipated Q&A

> *"Couldn't we do this in Postgres with recursive CTEs?"*
> Yes, but every variable-hop question becomes a custom rewrite, and performance falls off past
> 3–4 hops because each join re-scans. Graph traversal cost is local — independent of total table
> size.

> *"What if the team only knows SQL?"*
> They don't need Cypher. Claude writes it. They write the question.

> *"Is the graph the system of record for clinical data?"*
> No. iBKH is a reasoning layer over published biomedical sources — DrugBank, DisGeNET, others.
> It's a knowledge surface, not a database of patients.

---

## Staging tips

- Have Claude Desktop open with the `ibkh` server already loaded; verify the tools menu before
  starting.
- First tool call has a ~2s warmup — kick off question #1 right after the opening line so the
  pause is invisible.
- For Q3 the result will list many drugs — don't enumerate; point at the count and move on.
- If asked "what if it gets a question wrong?" — answer: it falls back to ad-hoc Cypher; the
  schema is exposed via `get_neo4j_schema` so it can ground its own queries.

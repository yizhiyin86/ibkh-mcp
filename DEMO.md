# iBKH Demo — Executive Script (~6 min)

A live walkthrough of the iBKH knowledge graph inside Claude. Five clinical questions, real biomedical answers, with one beat to explain why the underlying technology matters.

---

## Background

SLE patients commonly receive hydroxychloroquine (Plaquenil) from rheumatologists. For women of European descent there's a known ~20% risk of developing macular degeneration, leading to referrals to a retinal specialist. The genetic connections that may help explain that risk are now explorable — and a rheumatologist could use this to make a more informed prescribing decision before the first pill is ever taken.

---

## Open *(~30 sec)*
> Here's a real clinical scenario. A rheumatologist prescribes hydroxychloroquine — Plaquenil — to an SLE patient. It works. But for women of European descent, there's roughly a one-in-five chance that patient eventually develops macular degeneration. We've always known this happens — but tracing the genetic connections that might explain why has traditionally meant weeks of literature review, specialist consultations, and a fair amount of educated guesswork.
What I want to show you today is how a physician or a researcher can start exploring those connections in plain language — in seconds — using a biomedical knowledge graph built on Neo4j. For a clinician, it means asking 'is there a genetic reason this patient might be at higher risk?' and getting a biologically grounded starting point before writing the prescription. For a researcher, it means uncovering candidate drugs and genetic pathways that would otherwise take weeks of literature review to surface. The graph doesn't replace judgment — it makes the underlying biology easier to navigate, for anyone asking the question. Five questions. All live.

---

## 1. Is there a genetic connection at all? *(~45 sec)*

**Type:** `What genes do lupus and macular degeneration share?`

**Punchline:** Eight shared genes surface immediately. Four of them — **C2, C3, CFB, and SERPING1** — are core components of the complement system, the part of the immune response that drives tissue damage in both conditions. This isn't a coincidence — it's a plausible biological thread connecting why the same patient population may be vulnerable to both diseases.

---

## 2. Where does the drug fit in? *(~45 sec)*

**Type:** `Of those shared genes, which does hydroxychloroquine interact with?`

**Punchline:** One gene: **CCL2**. The graph shows hydroxychloroquine both interacts with and upregulates CCL2 — a gene involved in recruiting immune cells to inflamed tissue, including the retina. That's a concrete molecular thread worth exploring between the drug and the side effect.

---

## 3. Are there safer options for at-risk patients? *(~45 sec)*

**Type:** `What lupus drugs avoid the macular-degeneration gene network?`

**Punchline:** Out of nearly **3,845 lupus-related compounds** in the database, the system filters to those with no known connections to the AMD gene network. Drugs like belimumab, anifrolumab, and voclosporin come through — biologics that work through completely different pathways. A rheumatologist now has a principled starting point to consider these first for a patient already at elevated retinal risk.

---

## Pause — Why Does This Need a Graph Database? *(~45 sec)*

> "Quick aside — because someone will ask. Could you do this in a standard relational database? For simple lookups, yes. But even before we get to the complex questions, you're already paying a performance cost — every connection between drugs, genes, and diseases requires joins across multiple tables, and that overhead adds up quickly as the relationships multiply.
>
> Now add the next question: trace *indirect* biological connections — genes that influence other genes through one or two intermediate steps. In a relational database, variable-depth traversal like that means rewriting multiple queries every time you want to go one hop deeper, and performance falls off sharply because each join has to re-scan the full table. In Neo4j, traversal cost is local — the database follows the relationship directly, independent of how large the overall dataset is. The same question that would take three or four hand-stitched SQL queries is one line here. Watch."

---

## 4. How Deep Does the Biology Go? *(~45 sec)*

**Type:** `Find lupus genes that regulate macular-degeneration genes both directly and indirectly.`

**Punchline:** The system traces regulatory paths across one and two biological steps. New connections emerge — lupus-associated cytokines like **IL-6 and IL-18** reach AMD-associated genes through intermediate proteins. These aren't obvious links. Finding them through traditional literature review would take considerable time, and here it takes seconds — giving a physician a biologically coherent hypothesis they can bring to a specialist colleague.

---

## 5. How Big Is the Landscape? *(~30 sec)*

**Type:** `How many drugs treat lupus in total?`

**Punchline:** **3,845.** The system isn't limited to pre-written queries. Claude reads the underlying data structure and writes its own query on the fly. Any clinical question — any disease pair, any drug — gets the same treatment. The physician asks in plain English; the system handles the rest.

---

## Close *(~30 sec)*

> "Same workflow, any disease pair, any drug. A rheumatologist doesn't need to know anything about databases or bioinformatics. They type the question they'd ask a colleague. The system finds the connections, explains the biology, and flags the alternatives — giving the clinician a biologically grounded starting point in seconds rather than weeks. That's what this is: a reasoning layer that sits between a clinician's intuition and the published biomedical literature, and makes that gap easier to cross."

---

## Anticipated Q&A

> **"How reliable is this? Could it lead a physician astray?"**
>
> The knowledge graph draws from established published sources — DrugBank, DisGeNET, and others. It surfaces connections for a physician to investigate, not directives to act on. Think of it as a well-read colleague flagging something worth looking into, not a prescription pad.

> **"Does the doctor need to understand the technology?"**
>
> No. They type the clinical question. Claude reads the data structure and writes the query itself. The physician never sees code.

> **"Is this replacing clinical judgment?"**
>
> No. It gives a clinician a fast, biologically grounded starting point on a question that would traditionally require a literature review, a genetics consult, or a fortunate conversation at a conference.

---

## Staging Tips

- Have Claude open with the iBKH tools already loaded and verified before starting.
- The first query has a brief warmup — start it right after the opening line so the pause feels natural.
- For question 3, don't enumerate the drug list — point to the count and the clinical logic, then move on.
- If asked what happens with an unexpected question: Claude inspects the graph schema on the fly and writes its own query. It is not limited to the five shown here.

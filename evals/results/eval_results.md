# RAG Evaluation Results

**Judge model:** `openai/gpt-oss-20b` · **Config:** vector-only (production default), top_k=3 · **Corpus:** 16 energy-market documents · **Questions:** 8

## Average scores

| Metric | Score |
|---|---|
| Faithfulness | 0.975 |
| Answer Relevancy | 0.988 |
| Context Precision | 0.533 |
| Context Recall | 1.000 |

## Per-question

| # | Question | Faith. | Ans.Rel. | Ctx.Prec. | Ctx.Rec. |
|---|---|---|---|---|---|
| 1 | E.ON's two core business segments | 1.00 | 1.00 | 0.33 | 1.00 |
| 2 | RWE's renewables growth programme | 1.00 | 1.00 | 0.33 | 1.00 |
| 3 | Regions of RWE offshore wind farms | 1.00 | 1.00 | 0.33 | 1.00 |
| 4 | Vattenfall's stated mission | 1.00 | 1.00 | 0.33 | 1.00 |
| 5 | Vattenfall's district-heating cities | 1.00 | 0.90 | 0.50 | 1.00 |
| 6 | EnBW in the EV-charging market | 0.80 | 1.00 | 1.00 | 1.00 |
| 7 | EnBW / TransnetBW transmission (SuedLink) | 1.00 | 1.00 | 0.77 | 1.00 |
| 8 | Key regulatory frameworks | 1.00 | 1.00 | 0.67 | 1.00 |

## Note on retrieval strategy

A controlled A/B experiment (`eval_comparison.md`) compared plain vector search against
hybrid (BM25 + vector) retrieval with cross-encoder reranking, using the **same judge** for both.
On this clean, semantically-distinct corpus the strong `bge-small` embeddings already retrieve
optimally, and an off-the-shelf (MS-MARCO) reranker slightly **reduced** precision and recall.
The reranking pipeline is therefore kept implemented and configurable, but **disabled by default**;
it is expected to help on larger, noisier corpora. This is an evaluation-driven decision, not an
assumption.

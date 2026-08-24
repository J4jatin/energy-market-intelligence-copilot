# 🎓 Interview Study Guide — Energy Market Intelligence Copilot

Use this to defend the project **line-by-line** in interviews. Every answer here maps to real
code in the repo. Read it, then open the files and trace each claim yourself.

---

## 1. 30-second elevator pitch

> "It's an agentic RAG system for energy-market intelligence. You ask natural-language questions
> about competitors like RWE or Ørsted and it answers grounded in a document knowledge base,
> citing sources. It's built on LangChain v1 with LCEL, uses FastEmbed embeddings and a FAISS
> vector store, and generation runs on Groq. The part I'm most proud of is the **evaluation
> harness** — I score faithfulness, relevancy and retrieval precision on a golden set, and I ran
> a **controlled A/B test** that told me *not* to ship reranking on this corpus. There's also a
> LangGraph agent that decides when to search. It's Dockerised with CI."

---

## 2. Architecture, in one breath

Ingestion: documents → `RecursiveCharacterTextSplitter` (1000/200) → FastEmbed `bge-small-en-v1.5`
embeddings → FAISS index on disk. Query: retrieve top-k chunks → format with source labels →
build an LCEL `ChatPromptTemplate` (system + history + question) → Groq LLM → answer + sources.
The agent wraps retrieval as a tool and lets the model orchestrate calls.

---

## 3. Key design decisions & trade-offs (the "why")

| Decision | Why | Trade-off |
|---|---|---|
| **Groq (GPT-OSS)** not OpenAI | Free tier, OpenAI-compatible, fast | Free-tier rate/day limits; models rotate |
| **FastEmbed** not sentence-transformers | ONNX, no 800 MB torch, faster CPU, Qdrant-friendly | Slightly fewer model choices |
| **FAISS** | Simple, local, zero-infra, fast for this scale | Not a networked DB; would use Qdrant/pgvector at scale |
| **LCEL** not legacy chains | `ConversationalRetrievalChain` is removed in LangChain v1; LCEL is the current, composable API | Had to rewrite the engine |
| **Reranking OFF by default** | My A/B showed it *hurt* precision/recall on this clean corpus | Would enable it on large, noisy corpora |
| **LLM-as-judge eval** not RAGAS lib | RAGAS conflicted with LangChain v1; custom = transparent + no dep hell | I maintain the metric prompts myself |

---

## 4. Likely questions & strong answers

**Q: What is RAG and why use it?**
Retrieval-Augmented Generation grounds an LLM's answer in retrieved documents instead of relying on
its parametric memory. It reduces hallucination, lets you cite sources, and updates knowledge by
changing documents, not retraining.

**Q: Walk me through what happens when a user asks a question.**
`ask()` calls the retriever (`self._retriever.invoke(query)`) → gets top-k `Document`s → `_format_docs`
labels each with its source → the LCEL prompt is filled with context + chat history + question →
`ChatGroq.invoke()` generates the answer → I return the answer plus a structured `source_documents`
list. History is a bounded buffer (`memory_window`).

**Q: How does your chunking work and why those numbers?**
`RecursiveCharacterTextSplitter`, `chunk_size=1000`, `overlap=200`, splitting on paragraph → line →
sentence boundaries. 1000 chars balances enough context per chunk against retrieval precision;
200 overlap prevents a fact being split across a boundary.

**Q: Why FAISS, and what's an embedding?**
An embedding maps text to a vector so semantically similar text is nearby. FAISS does fast
nearest-neighbour search over those vectors. I use cosine/inner-product with normalised `bge-small`
embeddings. FAISS is in-process and perfect for this scale; at production scale I'd move to a
networked vector DB (Qdrant, pgvector).

**Q: What are the evaluation metrics, exactly?**
- *Faithfulness*: are the answer's claims supported by the retrieved context? (anti-hallucination)
- *Answer relevancy*: does the answer address the question?
- *Context precision*: what fraction of retrieved chunks are actually relevant?
- *Context recall*: does the retrieved context contain the facts needed for the reference answer?
Each is scored 0–1 by an LLM judge at temperature 0, over an 8-question golden set.

**Q: You added hybrid retrieval and reranking — did it help?**
No — and that's the point. I ran a controlled A/B with the same judge: vector-only vs. BM25+vector
ensemble + FlashRank reranking. On this clean corpus, reranking **lowered** precision (0.53 → 0.40)
and recall (1.0 → 0.875) because strong embeddings already retrieved well and the MS-MARCO reranker
was out-of-domain. So I kept it implemented but **disabled by default**. It's an evaluation-driven
decision — rerankers pay off on large, noisy corpora, not this one.

**Q: What makes it "agentic"?**
The LangGraph ReAct agent (`agent.py`) exposes retrieval as a `@tool`. The model decides whether and
how many times to call it, can search for multiple sub-topics, and combines results — versus the
plain RAG's single fixed retrieval. I track how many tool calls it made for transparency.

**Q: How is hallucination controlled?**
Grounding + citations + a system prompt that says "if it's not in the context, say so", and the
faithfulness metric quantifies it (0.975 in production).

**Q: How would you scale this to millions of documents?**
Swap FAISS for a networked vector DB (Qdrant/pgvector), move embeddings to a batch pipeline, add
caching (semantic cache), enable hybrid + reranking (now worth it at scale), add observability
(tracing) and async retrieval.

---

## 5. Files to know cold

- `src/chatbot/rag_engine.py` — retrieval + generation; know `_build_retriever`, `ask`, the LCEL prompt.
- `src/chatbot/agent.py` — the two tools and `create_react_agent`.
- `evals/evaluator.py` — the four metric prompts and the JSON score parser.
- `evals/run_eval.py` — single vs `--compare` A/B logic.
- `data_ingestion.py` — load → chunk → embed → FAISS.

---

## 6. Honest weaknesses (say these before they ask)

- Small synthetic corpus (16 docs) — chosen for a clean demo; real value shows at scale.
- LLM-as-judge has variance; I use temperature 0 and a fixed golden set to reduce it.
- No auth / multi-user; single-process FAISS. Both are deliberate scope choices for a portfolio demo.

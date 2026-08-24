# ⚡ Energy Market Intelligence Copilot

> An **agentic RAG** platform for the European energy sector — ask natural-language
> questions about competitors and market trends, grounded in a document knowledge base,
> with a **rigorous evaluation harness** and a **LangGraph tool-calling agent**.

Built with **Python · LangChain (v1, LCEL) · LangGraph · FAISS · FastEmbed · Groq (GPT-OSS) · Streamlit**, containerised with **Docker** and tested in **GitHub Actions CI**.

**🚀 Live demo:** [enterprise-search-rag-demo-bbwcfchydfbrfc54yh9ntd.streamlit.app](https://enterprise-search-rag-demo-bbwcfchydfbrfc54yh9ntd.streamlit.app)

---

## 🎯 What it does

| Capability | Description |
|---|---|
| 🔎 **RAG Q&A** | Ask about energy competitors (E.ON, RWE, Vattenfall, EnBW, Uniper, Ørsted, EDF, Octopus, Iberdrola) and market themes. Answers are grounded in retrieved documents and cite their sources. |
| 🤖 **Agentic mode** | A LangGraph ReAct agent decides *when* and *how often* to search the knowledge base, reasons across multiple retrievals, and combines tools before answering. |
| 📊 **Evaluation harness** | A dependency-free, RAGAS-style LLM-as-judge suite scoring **faithfulness, answer relevancy, context precision, context recall** over a golden question set — plus a **controlled A/B mode**. |
| 🧩 **Configurable retrieval** | Plain vector search by default; optional **hybrid (BM25 + vector) retrieval** and **cross-encoder reranking (FlashRank)** — kept or disabled based on measured results, not assumptions. |
| 📰 **Newsletter generator** | Renders an HTML competitive-intelligence newsletter from market data with an LLM executive summary. |

---

## 🏗️ Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │                Streamlit UI                  │
                    └───────────────┬──────────────────────────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              │                                            │
      ┌───────▼────────┐                        ┌──────────▼───────────┐
      │  RAG engine     │                        │  LangGraph agent      │
      │ (LCEL, vector)  │                        │ (ReAct, tool-calling) │
      └───────┬────────┘                        └──────────┬───────────┘
              │  retrieve                                    │ search_knowledge_base()
              ▼                                              ▼
      ┌────────────────────────────────────────────────────────────┐
      │  Retrieval layer                                           │
      │   FastEmbed (bge-small, ONNX)  →  FAISS vector index       │
      │   [optional] BM25 keyword + Ensemble + FlashRank rerank    │
      └────────────────────────────────────────────────────────────┘
              ▲                                              │
              │ ingest / chunk / embed                       ▼
      ┌───────┴────────┐                          ┌─────────────────────┐
      │ data/sample_docs│                          │  Groq (GPT-OSS) LLM │
      │ (16 briefs)     │                          │  answer generation  │
      └────────────────┘                          └─────────────────────┘
```

---

## 🚀 Quickstart

```bash
# 1. Create a virtual environment and install
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt

# 2. Configure your (free) Groq API key
copy .env.example .env            # then edit .env and set GROQ_API_KEY

# 3. Build the vector index from the sample knowledge base
python src/chatbot/data_ingestion.py

# 4a. Ask a question (plain RAG)
python -m src.chatbot.rag_engine

# 4b. Ask via the agent (tool-calling)
python -m src.chatbot.agent

# 4c. Launch the web app
streamlit run src/app.py
```

> **LLM:** this project uses **Groq**, which offers a free API tier (no credit card).
> Get a key at [console.groq.com](https://console.groq.com) and set `GROQ_API_KEY` in `.env`.

---

## 📊 Evaluation

Retrieval-augmented systems must be **measured**, not assumed. This repo ships a
dependency-free, RAGAS-style evaluator (`evals/`) that uses an LLM judge to score four
standard metrics over a golden question set.

```bash
python -m evals.run_eval            # score the current pipeline
python -m evals.run_eval --compare  # controlled A/B: vector-only vs. hybrid+rerank (same judge)
```

**Production results** (vector-only, 16-doc corpus, judge = `openai/gpt-oss-20b`):

| Metric | Score |
|---|---|
| Faithfulness | 0.975 |
| Answer relevancy | 0.988 |
| Context precision | 0.533 |
| Context recall | 1.000 |

**A/B finding (an evaluation-driven decision):** a controlled experiment comparing plain
vector search against hybrid retrieval + cross-encoder reranking — judged by the *same* model —
showed that on this clean, semantically-distinct corpus, the strong `bge-small` embeddings
already retrieve near-optimally, and an off-the-shelf (MS-MARCO) reranker **slightly reduced**
precision and recall. **Reranking is therefore implemented but disabled by default**, and is
expected to help on larger, noisier corpora. Full numbers: `evals/results/eval_comparison.md`.

---

## 🧠 Tech stack

| Layer | Technology |
|---|---|
| LLM | Groq (GPT-OSS, OpenAI-compatible, free tier) |
| Orchestration | LangChain v1 (LCEL runnables), LangGraph (ReAct agent) |
| Embeddings | FastEmbed — `bge-small-en-v1.5` (ONNX, no torch) |
| Vector store | FAISS |
| Hybrid / rerank | BM25 (`rank-bm25`) + EnsembleRetriever + FlashRank (optional) |
| Evaluation | Custom LLM-as-judge (RAGAS-style), golden set + A/B mode |
| UI | Streamlit |
| Tooling | Docker · docker-compose · GitHub Actions CI · pytest |

---

## 📁 Project structure

```
energy-market-intelligence-copilot/
├── src/
│   ├── chatbot/
│   │   ├── rag_engine.py       # LCEL RAG (vector + optional hybrid/rerank)
│   │   ├── agent.py            # LangGraph ReAct agent over the KB
│   │   ├── data_ingestion.py   # load → chunk → embed → FAISS
│   │   └── prompts.py
│   ├── newsletter/             # HTML newsletter generator + scraper
│   ├── automation/             # scheduled pipeline
│   └── app.py                  # Streamlit UI
├── evals/
│   ├── evaluator.py            # LLM-as-judge metrics
│   ├── run_eval.py             # single + A/B evaluation runner
│   ├── golden_set.json         # 8 reference Q&A pairs
│   └── results/                # saved scores (JSON + Markdown)
├── data/sample_docs/           # 16 energy-market knowledge documents
├── tests/                      # pytest suite (mocked, no network)
├── Dockerfile · docker-compose.yml
└── .github/workflows/ci.yml
```

---

## 🐳 Run with Docker

```bash
# Put your GROQ_API_KEY in .env first
docker compose up --build
# open http://localhost:8501
```

---

## 🧪 Tests

```bash
pytest tests/ -v
```

All tests are mocked (no network, no API key needed) and run automatically in CI on every push.

---

## 📄 License

MIT

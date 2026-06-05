# ⚡ Energy Market Intelligence Copilot

> AI-powered competitive intelligence platform for the energy sector — RAG chatbot + automated HTML newsletter generation + Python workflow automation.

Built with Python, LangChain, FAISS, Streamlit, and Azure DevOps CI/CD.

---

## 🎯 What It Does

| Feature | Description |
|---|---|
| 🤖 **RAG Chatbot** | Ask natural-language questions about energy market competitors (E.ON, RWE, Vattenfall, EnBW). Answers grounded in real documents. |
| 📰 **Newsletter Generator** | Auto-generates polished HTML competitive intelligence newsletters from live RSS feeds + internal reports |
| ⚙️ **Workflow Automation** | Scheduled Python pipeline — runs daily, scrapes data, updates vector store, sends newsletter |
| 🏢 **SharePoint Integration** | Publishes generated newsletters directly to MS SharePoint hub |
| 🔄 **Azure DevOps CI/CD** | Full pipeline — lint, test, deploy on every push |

---

## 🏗️ Architecture

```
energy-market-intelligence-copilot/
├── src/
│   ├── chatbot/
│   │   ├── rag_engine.py        # LangChain + FAISS RAG engine
│   │   ├── data_ingestion.py    # Document loader & chunker
│   │   └── prompts.py           # System prompts
│   ├── newsletter/
│   │   ├── generator.py         # HTML newsletter builder
│   │   ├── scraper.py           # RSS + web scraper
│   │   └── sharepoint_uploader.py  # MS SharePoint integration
│   ├── automation/
│   │   ├── scheduler.py         # Daily automation pipeline
│   │   └── pipeline.py          # Orchestrator
│   └── app.py                   # Streamlit UI
├── templates/
│   └── newsletter.html          # Jinja2 HTML template
├── data/
│   └── sample_docs/             # Sample energy market reports
├── tests/
│   ├── test_rag.py
│   └── test_newsletter.py
├── azure-pipelines.yml          # Azure DevOps CI/CD
├── .env.example
└── requirements.txt
```

---

## 🚀 Quick Start

```bash
# 1. Clone & install
git clone https://github.com/J4jatin/energy-market-intelligence-copilot
cd energy-market-intelligence-copilot
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Add your OpenAI API key + SharePoint credentials

# 3. Ingest documents into vector store
python src/chatbot/data_ingestion.py

# 4. Launch the app
streamlit run src/app.py
```

---

## 🤖 RAG Chatbot — How It Works

1. **Ingest**: PDF/TXT energy market reports are chunked and embedded using `sentence-transformers`
2. **Store**: Embeddings stored in FAISS vector index (local, no cloud needed)
3. **Retrieve**: On each question, top-k relevant chunks are retrieved
4. **Generate**: LLM generates answer grounded in retrieved context

```python
# Example usage
from src.chatbot.rag_engine import MarketIntelligenceRAG

rag = MarketIntelligenceRAG()
answer = rag.ask("What is RWE's current renewable energy capacity?")
print(answer)
```

---

## 📰 Newsletter Generator — How It Works

1. **Scrape**: Pulls latest news from energy sector RSS feeds (Reuters Energy, Bloomberg NEF, etc.)
2. **Summarize**: LLM summarizes articles by competitor
3. **Render**: Jinja2 renders polished HTML newsletter
4. **Publish**: Auto-uploads to SharePoint or sends via email

```python
from src.newsletter.generator import NewsletterGenerator

gen = NewsletterGenerator()
html = gen.generate(topic="German energy market Q2 2025")
gen.save("newsletter_2025_Q2.html")
```

---

## ⚙️ Automation Pipeline

Runs daily at 07:00 via `schedule`:

```
[07:00] Scrape RSS feeds → Summarize → Update FAISS index
[07:05] Generate HTML newsletter
[07:10] Upload to SharePoint
[07:15] Send digest email
```

---

## 🔧 Tech Stack

| Layer | Tech |
|---|---|
| AI / RAG | LangChain, FAISS, Sentence Transformers, OpenAI GPT-4o |
| Automation | Python `schedule`, custom pipeline orchestrator |
| Newsletter | Jinja2, HTML/CSS, Premailer (email-safe CSS) |
| Microsoft | SharePoint REST API, MSAL authentication |
| CI/CD | Azure DevOps Pipelines |
| UI | Streamlit |
| Testing | pytest |

---

## 🏢 Relevant Use Cases

- **Market Intelligence teams** tracking competitor pricing, capacity expansions, regulatory changes
- **Internal knowledge bases** — ask questions against proprietary research reports
- **Weekly automated briefings** delivered to stakeholders via email or SharePoint

---

## 📊 Energy Competitors Tracked

- E.ON (Germany)
- RWE AG
- Vattenfall
- Uniper
- EnBW Energie Baden-Württemberg
- Octopus Energy
- EDF

---

## 🔐 Environment Variables

```env
OPENAI_API_KEY=your_key_here
SHAREPOINT_SITE_URL=https://yourtenant.sharepoint.com/sites/MarketIntelligence
SHAREPOINT_CLIENT_ID=your_client_id
SHAREPOINT_CLIENT_SECRET=your_client_secret
SHAREPOINT_TENANT_ID=your_tenant_id
EMAIL_SMTP_HOST=smtp.office365.com
EMAIL_SMTP_USER=your_email
EMAIL_SMTP_PASS=your_password
```

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## 📄 License

MIT

"""
Streamlit UI for the Energy Market Intelligence Copilot.

Features:
  - RAG chatbot tab for natural language Q&A
  - Newsletter generator tab with live HTML preview
  - Pipeline status / run history
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# Make sure the project root (parent of this src/ folder) is importable as "src.*"
# regardless of how/where this script is launched from (needed on Streamlit Cloud).
sys.path.insert(0, str(Path(__file__).parent.parent))

# Page config — must be first Streamlit call
st.set_page_config(
    page_title="Energy Market Intelligence Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

logger = logging.getLogger(__name__)

# ── Lazy imports (avoid errors if deps not installed) ──────────────────────────
@st.cache_resource(show_spinner="Loading RAG engine...")
def load_rag():
    try:
        from src.chatbot.rag_engine import MarketIntelligenceRAG
        return MarketIntelligenceRAG()
    except Exception as e:
        logger.error(f"RAG load error: {e}")
        return None


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ Market Intelligence")
    st.markdown("---")
    st.markdown("**Competitors tracked:**")
    competitors = ["E.ON", "RWE", "Vattenfall", "Uniper", "EDF", "Octopus Energy"]
    for c in competitors:
        st.markdown(f"  • {c}")
    st.markdown("---")

    if st.button("🔄 Run Pipeline Now", use_container_width=True):
        with st.spinner("Running pipeline..."):
            try:
                from src.automation.pipeline import MarketIntelligencePipeline
                pipeline = MarketIntelligencePipeline()
                result = pipeline.run(upload_to_sharepoint=False)
                if result["status"] == "completed":
                    st.success(
                        f"✅ Done! {result['articles_processed']} articles, "
                        f"{result['duration_seconds']}s"
                    )
                    st.session_state["last_pipeline_result"] = result
                else:
                    st.error(f"Pipeline failed: {result['errors']}")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown(
        "<small>Built with Python · LangChain · FAISS<br>"
        "Azure DevOps CI/CD · MS SharePoint</small>",
        unsafe_allow_html=True,
    )


# ── Main Tabs ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🤖 RAG Chatbot", "📰 Newsletter", "⚙️ Pipeline"])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: RAG CHATBOT
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("## 🤖 Market Intelligence Chatbot")
    st.markdown(
        "Ask questions about European energy competitors, market trends, "
        "pricing dynamics, and regulatory changes — answers grounded in your documents."
    )

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Example questions
    st.markdown("**Try asking:**")
    example_cols = st.columns(3)
    examples = [
        "What is RWE's offshore wind strategy?",
        "How is E.ON expanding in renewables?",
        "What are current German electricity prices?",
    ]
    for i, (col, q) in enumerate(zip(example_cols, examples)):
        if col.button(q, key=f"ex_{i}", use_container_width=True):
            st.session_state["prefill_question"] = q

    st.markdown("---")

    # Chat input
    prefill = st.session_state.pop("prefill_question", "")
    user_question = st.chat_input(
        "Ask about energy market competitors...",
    )
    if prefill and not user_question:
        user_question = prefill

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📄 Sources"):
                    for src in msg["sources"]:
                        st.markdown(
                            f"**{src.get('source', 'Unknown')}** "
                            f"(page {src.get('page', 'N/A')}): "
                            f"_{src.get('snippet', '')}..._"
                        )

    # Process new question
    if user_question:
        st.session_state.chat_history.append(
            {"role": "user", "content": user_question}
        )
        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                rag = load_rag()
                if rag and rag.is_ready:
                    result = rag.ask(user_question)
                    answer = result["answer"]
                    sources = result.get("source_documents", [])
                else:
                    answer = (
                        "⚠️ The knowledge base is not yet initialized. "
                        "Please run `python src/chatbot/data_ingestion.py` first "
                        "to ingest your market reports."
                    )
                    sources = []

            st.markdown(answer)
            if sources:
                with st.expander("📄 Sources"):
                    for src in sources:
                        st.markdown(
                            f"**{src.get('source', 'Unknown')}** "
                            f"(page {src.get('page', 'N/A')}): "
                            f"_{src.get('snippet', '')}_"
                        )

        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer, "sources": sources}
        )

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑 Clear conversation"):
            st.session_state.chat_history = []
            rag = load_rag()
            if rag:
                rag.reset_memory()
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: NEWSLETTER GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("## 📰 Newsletter Generator")
    st.markdown(
        "Automatically scrape energy market news and generate a polished "
        "HTML competitive intelligence newsletter."
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Settings")
        max_age = st.slider("News age (days)", 1, 14, 7)
        include_ai_summary = st.checkbox("Include AI executive summary", value=True)
        upload_sp = st.checkbox("Upload to SharePoint after generation", value=False)

        generate_btn = st.button("⚡ Generate Newsletter", type="primary", use_container_width=True)

    with col2:
        if generate_btn:
            with st.spinner("Scraping feeds & generating newsletter..."):
                try:
                    from src.newsletter.generator import (
                        NewsletterGenerator,
                        generate_ai_summary,
                    )
                    from src.newsletter.scraper import get_market_snapshot

                    snapshot = get_market_snapshot()
                    ai_summary = generate_ai_summary(snapshot) if include_ai_summary else ""
                    gen = NewsletterGenerator()
                    html = gen.generate(snapshot, ai_summary)
                    output_path = gen.save(html)

                    st.session_state["newsletter_html"] = html
                    st.session_state["newsletter_path"] = str(output_path)
                    st.session_state["newsletter_snapshot"] = snapshot

                    st.success(
                        f"✅ Newsletter generated! "
                        f"{snapshot['total_articles']} articles across "
                        f"{len(snapshot['categories'])} categories."
                    )

                    if upload_sp:
                        from src.newsletter.sharepoint_uploader import (
                            SharePointUploader,
                        )
                        url = SharePointUploader().upload(output_path)
                        if url:
                            st.success(f"📤 Uploaded to SharePoint: {url}")

                except Exception as e:
                    st.error(f"Generation failed: {e}")

        # Show preview
        if "newsletter_html" in st.session_state:
            st.markdown("### Preview")
            components.html(
                st.session_state["newsletter_html"],
                height=600,
                scrolling=True,
            )
            st.download_button(
                "⬇️ Download HTML",
                data=st.session_state["newsletter_html"],
                file_name=Path(st.session_state["newsletter_path"]).name,
                mime="text/html",
                use_container_width=True,
            )
        else:
            st.info("Click 'Generate Newsletter' to preview it here.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: PIPELINE STATUS
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("## ⚙️ Automation Pipeline")

    col1, col2, col3 = st.columns(3)
    col1.metric("Schedule", "Daily @ 07:00")
    col2.metric("Status", "Running" if True else "Stopped")
    col3.metric("Last Run", datetime.now().strftime("%Y-%m-%d"))

    st.markdown("---")

    if "last_pipeline_result" in st.session_state:
        r = st.session_state["last_pipeline_result"]
        st.markdown("### Last Pipeline Run")
        st.json(r)

    st.markdown("### Pipeline Steps")
    steps = [
        ("📡", "Scrape RSS feeds", "Reuters Energy, Bloomberg NEF, Recharge News, PV Magazine"),
        ("🏷️", "Categorize by competitor", "E.ON, RWE, Vattenfall, Uniper, EDF, General"),
        ("🤖", "Generate AI summary", "GPT-4o-mini executive summary"),
        ("🎨", "Render HTML newsletter", "Jinja2 template → email-safe HTML"),
        ("💾", "Save to disk", "data/newsletters/newsletter_YYYY_WXX.html"),
        ("🏢", "Upload to SharePoint", "Microsoft Graph API via MSAL OAuth2"),
    ]
    for icon, title, desc in steps:
        with st.expander(f"{icon} {title}"):
            st.markdown(desc)

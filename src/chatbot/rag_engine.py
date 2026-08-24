"""
RAG (Retrieval-Augmented Generation) engine for Market Intelligence Q&A.

Modern LangChain (v1) implementation using LCEL runnables:
  FastEmbed embeddings + FAISS retrieval + Groq (GPT-OSS) generation,
with a lightweight conversation-history buffer for multi-turn Q&A.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_classic.retrievers import (
    ContextualCompressionRetriever,
    EnsembleRetriever,
)
from langchain_community.document_compressors import FlashrankRerank
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from .prompts import NO_CONTEXT_RESPONSE, SYSTEM_PROMPT

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
INDEX_DIR = DATA_DIR / "faiss_index"


class MarketIntelligenceRAG:
    """
    Conversational RAG chatbot for energy market intelligence.

    Example:
        rag = MarketIntelligenceRAG()
        result = rag.ask("What is RWE's current offshore wind strategy?")
        print(result["answer"])
    """

    def __init__(
        self,
        model_name: str | None = None,
        temperature: float = 0.1,
        top_k: int = 3,
        memory_window: int = 5,
        hybrid: bool = False,
        rerank: bool = False,
        candidate_k: int = 8,
    ):
        self.model_name = model_name or os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        self.temperature = temperature
        self.top_k = top_k
        self.memory_window = memory_window
        # Retrieval strategy — configurable and evaluation-driven.
        # NOTE: a controlled A/B (see evals/results/eval_comparison.md) showed that on this
        # clean, semantically-distinct corpus, strong embeddings already retrieve optimally, and
        # an off-the-shelf (MS-MARCO) reranker slightly HURT precision/recall. So hybrid + rerank
        # default OFF here; enable them for larger, noisier corpora where they typically help.
        self.hybrid = hybrid          # BM25 keyword + vector ensemble
        self.rerank = rerank          # cross-encoder (FlashRank) reranking of candidates
        self.candidate_k = candidate_k  # candidates pulled before reranking down to top_k

        self._embeddings = None
        self._vectorstore = None
        self._retriever = None
        self._llm = None
        self._prompt = None
        self._history: list = []  # list of (human, ai) tuples
        self._is_ready = False

        self._initialize()

    def _initialize(self):
        """Load embeddings, vector store, LLM, and prompt."""
        try:
            self._embeddings = self._load_embeddings()
            self._vectorstore = self._load_vectorstore()
            self._retriever = self._build_retriever()
            self._llm = ChatGroq(
                model=self.model_name,
                temperature=self.temperature,
                groq_api_key=os.getenv("GROQ_API_KEY"),
                max_retries=6,
            )
            self._prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", SYSTEM_PROMPT),
                    ("placeholder", "{history}"),
                    ("human", "{question}"),
                ]
            )
            self._is_ready = True
            logger.info("✅ RAG engine initialized successfully")
        except FileNotFoundError:
            logger.warning(
                "⚠️  FAISS index not found. Run data_ingestion.py first:\n"
                "   python src/chatbot/data_ingestion.py"
            )
            self._is_ready = False
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            self._is_ready = False

    def _load_embeddings(self) -> FastEmbedEmbeddings:
        """Load local FastEmbed embeddings (ONNX, no API key, no torch)."""
        return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

    def _load_vectorstore(self) -> FAISS:
        """Load FAISS index from disk."""
        if not (INDEX_DIR / "index.faiss").exists():
            raise FileNotFoundError(f"No FAISS index at {INDEX_DIR}")
        return FAISS.load_local(
            str(INDEX_DIR),
            self._embeddings,
            allow_dangerous_deserialization=True,
        )

    def _build_retriever(self):
        """
        Build the retrieval pipeline:

            (1) vector search (FastEmbed + FAISS)
            (2) + BM25 keyword search, fused via an EnsembleRetriever   [hybrid]
            (3) + cross-encoder reranking (FlashRank) of the candidates [rerank]

        Reranking selects the best `top_k` chunks from `candidate_k` candidates,
        which sharply raises context precision over plain vector search.
        """
        k = self.candidate_k if self.rerank else self.top_k
        vector_retriever = self._vectorstore.as_retriever(search_kwargs={"k": k})

        base = vector_retriever
        if self.hybrid:
            docs = list(self._vectorstore.docstore._dict.values())
            if docs:
                bm25 = BM25Retriever.from_documents(docs)
                bm25.k = k
                base = EnsembleRetriever(
                    retrievers=[bm25, vector_retriever],
                    weights=[0.4, 0.6],  # favour semantic vector search, keep keyword recall
                )

        if self.rerank:
            compressor = FlashrankRerank(top_n=self.top_k)
            return ContextualCompressionRetriever(
                base_compressor=compressor, base_retriever=base
            )
        return base

    @staticmethod
    def _format_docs(docs) -> str:
        """Concatenate retrieved chunks with their source labels for grounding."""
        return "\n\n".join(
            f"[Source: {d.metadata.get('source', 'Unknown')}]\n{d.page_content}"
            for d in docs
        )

    def ask(self, question: str) -> dict:
        """
        Ask a question against the market-intelligence knowledge base.

        Returns:
            dict with keys: answer (str), source_documents (list[dict])
        """
        if not self._is_ready:
            return {"answer": NO_CONTEXT_RESPONSE, "source_documents": []}

        try:
            docs = self._retriever.invoke(question)
            context = self._format_docs(docs)

            history_msgs = []
            for human, ai in self._history[-self.memory_window:]:
                history_msgs.append(HumanMessage(content=human))
                history_msgs.append(AIMessage(content=ai))

            messages = self._prompt.format_messages(
                context=context, history=history_msgs, question=question
            )
            answer = self._llm.invoke(messages).content
            self._history.append((question, answer))

            sources = [
                {
                    "source": d.metadata.get("source", "Unknown"),
                    "page": d.metadata.get("page", "N/A"),
                    "snippet": d.page_content[:200] + "...",
                }
                for d in docs
            ]
            return {"answer": answer, "source_documents": sources}
        except Exception as e:
            logger.error(f"Error during RAG query: {e}")
            return {"answer": f"Error processing your question: {e}", "source_documents": []}

    def reset_memory(self):
        """Clear conversation history."""
        self._history = []
        logger.info("Conversation memory cleared")

    def get_similar_documents(self, query: str, k: int = 3) -> list:
        """
        Retrieve the documents the full pipeline (hybrid + rerank) would use for a
        query, without generating an answer. Used by the evaluation harness so the
        metrics reflect the real retrieval strategy.
        """
        if not self._is_ready:
            return []
        return self._retriever.invoke(query)

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def reload_index(self):
        """Reload the FAISS index (e.g. after ingesting new documents)."""
        self._vectorstore = self._load_vectorstore()
        self._retriever = self._build_retriever()
        self._is_ready = True
        logger.info("Index reloaded")


if __name__ == "__main__":
    rag = MarketIntelligenceRAG()
    if rag.is_ready:
        result = rag.ask("What are the main renewable energy strategies of E.ON?")
        print("\n📊 Answer:", result["answer"])
        print("\n📄 Sources:")
        for src in result["source_documents"]:
            print(f"  - {src['source']} (page {src['page']})")
    else:
        print("Run data_ingestion.py first to build the knowledge base.")

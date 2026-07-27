"""
RAG (Retrieval-Augmented Generation) engine for Market Intelligence Q&A.

Modern LangChain (v1) implementation using LCEL runnables:
  FastEmbed embeddings + FAISS retrieval + Groq (Llama 3.3 70B) generation,
with a lightweight conversation-history buffer for multi-turn Q&A.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq

from .prompts import SYSTEM_PROMPT, NO_CONTEXT_RESPONSE

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
        model_name: Optional[str] = None,
        temperature: float = 0.1,
        top_k: int = 5,
        memory_window: int = 5,
    ):
        self.model_name = model_name or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.temperature = temperature
        self.top_k = top_k
        self.memory_window = memory_window

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
            self._retriever = self._vectorstore.as_retriever(
                search_kwargs={"k": self.top_k}
            )
            self._llm = ChatGroq(
                model=self.model_name,
                temperature=self.temperature,
                groq_api_key=os.getenv("GROQ_API_KEY"),
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
        """Retrieve top-k similar documents without generating an answer."""
        if not self._is_ready:
            return []
        return self._vectorstore.similarity_search(query, k=k)

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def reload_index(self):
        """Reload the FAISS index (e.g. after ingesting new documents)."""
        self._vectorstore = self._load_vectorstore()
        self._retriever = self._vectorstore.as_retriever(
            search_kwargs={"k": self.top_k}
        )
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

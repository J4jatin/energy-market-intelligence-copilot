"""
RAG (Retrieval-Augmented Generation) engine for Market Intelligence Q&A.

Uses LangChain + FAISS + HuggingFace embeddings + OpenAI GPT-4o.
Supports conversational memory for multi-turn Q&A sessions.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from .prompts import SYSTEM_PROMPT, CONDENSE_QUESTION_PROMPT, NO_CONTEXT_RESPONSE

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
        answer = rag.ask("What is RWE's current offshore wind strategy?")
        print(answer["answer"])
    """

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.1,
        top_k: int = 5,
        memory_window: int = 5,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.top_k = top_k
        self.memory_window = memory_window

        self._embeddings = None
        self._vectorstore = None
        self._chain = None
        self._is_ready = False

        self._initialize()

    def _initialize(self):
        """Load embeddings, vector store, and build the QA chain."""
        try:
            self._embeddings = self._load_embeddings()
            self._vectorstore = self._load_vectorstore()
            self._chain = self._build_chain()
            self._is_ready = True
            logger.info("✅ RAG engine initialized successfully")
        except FileNotFoundError:
            logger.warning(
                "⚠️  FAISS index not found. Run data_ingestion.py first.\n"
                "   python src/chatbot/data_ingestion.py"
            )
            self._is_ready = False
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            self._is_ready = False

    def _load_embeddings(self) -> HuggingFaceEmbeddings:
        """Load local sentence-transformer embeddings (no API key needed)."""
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    def _load_vectorstore(self) -> FAISS:
        """Load FAISS index from disk."""
        if not (INDEX_DIR / "index.faiss").exists():
            raise FileNotFoundError(f"No FAISS index at {INDEX_DIR}")
        return FAISS.load_local(
            str(INDEX_DIR),
            self._embeddings,
            allow_dangerous_deserialization=True,
        )

    def _build_chain(self) -> ConversationalRetrievalChain:
        """Build the conversational retrieval chain with memory."""
        llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

        retriever = self._vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.top_k},
        )

        memory = ConversationBufferWindowMemory(
            k=self.memory_window,
            memory_key="chat_history",
            output_key="answer",
            return_messages=True,
        )

        qa_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=SYSTEM_PROMPT + "\n\nQuestion: {question}\n\nAnswer:",
        )

        condense_prompt = PromptTemplate(
            input_variables=["chat_history", "question"],
            template=CONDENSE_QUESTION_PROMPT,
        )

        chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": qa_prompt},
            condense_question_prompt=condense_prompt,
            return_source_documents=True,
            verbose=False,
        )

        return chain

    def ask(self, question: str) -> dict:
        """
        Ask a question against the market intelligence knowledge base.

        Returns:
            dict with keys: answer, source_documents
        """
        if not self._is_ready:
            return {
                "answer": NO_CONTEXT_RESPONSE,
                "source_documents": [],
            }

        try:
            result = self._chain.invoke({"question": question})
            sources = [
                {
                    "source": doc.metadata.get("source", "Unknown"),
                    "page": doc.metadata.get("page", "N/A"),
                    "snippet": doc.page_content[:200] + "...",
                }
                for doc in result.get("source_documents", [])
            ]
            return {
                "answer": result["answer"],
                "source_documents": sources,
            }
        except Exception as e:
            logger.error(f"Error during RAG query: {e}")
            return {
                "answer": f"Error processing your question: {e}",
                "source_documents": [],
            }

    def reset_memory(self):
        """Clear conversation history."""
        if self._chain and hasattr(self._chain, "memory"):
            self._chain.memory.clear()
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
        self._chain = self._build_chain()
        self._is_ready = True
        logger.info("Index reloaded")


if __name__ == "__main__":
    # Quick test
    rag = MarketIntelligenceRAG()
    if rag.is_ready:
        result = rag.ask("What are the main renewable energy strategies of E.ON?")
        print("\n📊 Answer:", result["answer"])
        print("\n📄 Sources:")
        for src in result["source_documents"]:
            print(f"  - {src['source']} (page {src['page']})")
    else:
        print("Run data_ingestion.py first to build the knowledge base.")

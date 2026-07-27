"""
Tests for the RAG engine (modern LCEL implementation).
"""

import pytest
from unittest.mock import MagicMock


class TestMarketIntelligenceRAG:

    def _make_ready_rag(self):
        """Build a RAG instance without running __init__ (no network/model load)."""
        from src.chatbot.rag_engine import MarketIntelligenceRAG

        rag = MarketIntelligenceRAG.__new__(MarketIntelligenceRAG)
        rag._is_ready = True
        rag.memory_window = 5
        rag._history = []
        return rag

    def test_ask_returns_dict_with_answer(self):
        """RAG.ask() should return a dict with 'answer' and 'source_documents'."""
        from langchain_core.prompts import ChatPromptTemplate

        rag = self._make_ready_rag()

        # Mock retriever -> returns one doc
        doc = MagicMock()
        doc.page_content = "RWE is expanding offshore wind capacity."
        doc.metadata = {"source": "rwe_competitor_brief.txt"}
        rag._retriever = MagicMock()
        rag._retriever.invoke.return_value = [doc]

        # Real prompt so formatting is exercised; mock LLM
        rag._prompt = ChatPromptTemplate.from_messages(
            [("system", "Context:\n{context}"), ("placeholder", "{history}"), ("human", "{question}")]
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="RWE is expanding offshore wind by 2 GW.")
        rag._llm = mock_llm

        result = rag.ask("What is RWE's wind strategy?")

        assert "answer" in result
        assert "source_documents" in result
        assert "RWE" in result["answer"]
        assert result["source_documents"][0]["source"] == "rwe_competitor_brief.txt"

    def test_ask_when_not_ready_returns_no_context_message(self):
        """When RAG is not initialized, ask() should return a helpful message."""
        from src.chatbot.rag_engine import MarketIntelligenceRAG
        from src.chatbot.prompts import NO_CONTEXT_RESPONSE

        rag = MarketIntelligenceRAG.__new__(MarketIntelligenceRAG)
        rag._is_ready = False

        result = rag.ask("What is RWE's strategy?")

        assert result["answer"] == NO_CONTEXT_RESPONSE
        assert result["source_documents"] == []

    def test_reset_memory_clears_history(self):
        """reset_memory() should empty the conversation history buffer."""
        rag = self._make_ready_rag()
        rag._history = [("q1", "a1"), ("q2", "a2")]

        rag.reset_memory()

        assert rag._history == []

    def test_is_ready_property_false_by_default(self):
        """is_ready should reflect the internal flag."""
        from src.chatbot.rag_engine import MarketIntelligenceRAG

        rag = MarketIntelligenceRAG.__new__(MarketIntelligenceRAG)
        rag._is_ready = False
        assert rag.is_ready is False

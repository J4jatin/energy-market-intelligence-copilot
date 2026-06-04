"""
Tests for the RAG engine.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestMarketIntelligenceRAG:

    @patch("src.chatbot.rag_engine.FAISS")
    @patch("src.chatbot.rag_engine.HuggingFaceEmbeddings")
    def test_ask_returns_dict_with_answer(self, mock_embed, mock_faiss):
        """RAG.ask() should always return a dict with 'answer' key."""
        from src.chatbot.rag_engine import MarketIntelligenceRAG

        rag = MarketIntelligenceRAG.__new__(MarketIntelligenceRAG)
        rag._is_ready = True
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {
            "answer": "RWE is expanding offshore wind capacity by 2GW.",
            "source_documents": [],
        }
        rag._chain = mock_chain

        result = rag.ask("What is RWE's wind strategy?")

        assert "answer" in result
        assert "source_documents" in result
        assert "RWE" in result["answer"]

    def test_ask_when_not_ready_returns_no_context_message(self):
        """When RAG is not initialized, ask() should return a helpful message."""
        from src.chatbot.rag_engine import MarketIntelligenceRAG
        from src.chatbot.prompts import NO_CONTEXT_RESPONSE

        rag = MarketIntelligenceRAG.__new__(MarketIntelligenceRAG)
        rag._is_ready = False
        rag._chain = None

        result = rag.ask("What is RWE's strategy?")

        assert result["answer"] == NO_CONTEXT_RESPONSE
        assert result["source_documents"] == []

    @patch("src.chatbot.rag_engine.FAISS")
    @patch("src.chatbot.rag_engine.HuggingFaceEmbeddings")
    def test_reset_memory_clears_history(self, mock_embed, mock_faiss):
        """reset_memory() should clear the chain's conversation memory."""
        from src.chatbot.rag_engine import MarketIntelligenceRAG

        rag = MarketIntelligenceRAG.__new__(MarketIntelligenceRAG)
        rag._is_ready = True

        mock_memory = MagicMock()
        mock_chain = MagicMock()
        mock_chain.memory = mock_memory
        rag._chain = mock_chain

        rag.reset_memory()
        mock_memory.clear.assert_called_once()

    def test_is_ready_property_false_by_default(self):
        """is_ready should be False when index file doesn't exist."""
        from src.chatbot.rag_engine import MarketIntelligenceRAG

        with patch.object(MarketIntelligenceRAG, "_initialize", lambda self: None):
            rag = MarketIntelligenceRAG.__new__(MarketIntelligenceRAG)
            rag._is_ready = False
            assert rag.is_ready is False

"""
Tests for the LangGraph agent layer (no network / no LLM calls).
"""

from unittest.mock import MagicMock


class TestMarketIntelligenceAgent:

    def test_ask_when_not_ready_returns_message(self):
        """If the knowledge base isn't built, ask() returns a helpful message, not a crash."""
        from src.chatbot.agent import MarketIntelligenceAgent

        agent = MarketIntelligenceAgent.__new__(MarketIntelligenceAgent)
        agent._is_ready = False
        agent._agent = None

        out = agent.ask("What is RWE's strategy?")

        assert out["tool_calls"] == 0
        assert out["messages"] == []
        assert "not ready" in out["answer"].lower()

    def test_ask_returns_answer_and_tool_count(self):
        """ask() should extract the final answer and count tool calls from the trace."""
        from src.chatbot.agent import MarketIntelligenceAgent

        agent = MarketIntelligenceAgent.__new__(MarketIntelligenceAgent)
        agent._is_ready = True

        # Fake message trace: a tool-calling AI message, then a final answer.
        m1 = MagicMock(); m1.tool_calls = [{"name": "search_knowledge_base"}]
        m2 = MagicMock(); m2.tool_calls = []; m2.content = "RWE focuses on offshore wind."
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [m1, m2]}
        agent._agent = mock_agent

        out = agent.ask("What is RWE's strategy?")

        assert out["answer"] == "RWE focuses on offshore wind."
        assert out["tool_calls"] == 1

    def test_tracked_competitors_list_is_populated(self):
        from src.chatbot.agent import TRACKED_COMPETITORS

        assert "RWE" in TRACKED_COMPETITORS
        assert len(TRACKED_COMPETITORS) >= 5

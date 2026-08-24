"""
Agentic layer for the Market Intelligence Copilot.

Wraps the RAG retriever as a LangGraph tool-calling (ReAct) agent. Instead of a
single fixed retrieval, the model decides *when* and *how many times* to search
the knowledge base, can reason across multiple retrievals and sub-questions, and
can combine tools before answering.

Built with LangGraph's prebuilt ReAct agent + Groq (GPT-OSS).

Run:
    python -m src.chatbot.agent
"""

import logging
import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from .rag_engine import MarketIntelligenceRAG

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = (
    "You are an energy-market intelligence analyst assistant for a German energy company. "
    "Ground every factual claim by calling the `search_knowledge_base` tool before you answer. "
    "You may call it multiple times to gather information on different competitors or sub-topics. "
    "Use `list_tracked_competitors` if the user asks who is covered. "
    "If the knowledge base does not contain the answer, say so clearly instead of guessing. "
    "Be concise and analytical, and cite the source documents you used."
)

TRACKED_COMPETITORS = [
    "E.ON", "RWE", "Vattenfall", "EnBW", "Uniper",
    "Ørsted", "EDF", "Octopus Energy", "Iberdrola",
]


class MarketIntelligenceAgent:
    """
    ReAct agent over the energy-market knowledge base.

    Example:
        agent = MarketIntelligenceAgent()
        out = agent.ask("Compare RWE and Ørsted on offshore wind.")
        print(out["answer"])
    """

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        self._rag = MarketIntelligenceRAG()
        self._is_ready = self._rag.is_ready
        self._agent = self._build_agent() if self._is_ready else None

    def _build_agent(self):
        rag = self._rag  # closed over by the tools below

        @tool
        def search_knowledge_base(query: str) -> str:
            """Search the energy-market document knowledge base and return the most
            relevant passages with their source filenames. Use this to ground answers
            in real documents before responding."""
            docs = rag.get_similar_documents(query, k=rag.top_k)
            if not docs:
                return "No relevant documents found for that query."
            return "\n\n".join(
                f"[Source: {d.metadata.get('source', 'Unknown')}]\n{d.page_content}"
                for d in docs
            )

        @tool
        def list_tracked_competitors(reason: str = "user asked") -> str:
            """Return the list of energy companies currently covered in the knowledge base.

            Args:
                reason: Why you're calling this (e.g. "user asked which companies are covered").
            """
            return ", ".join(TRACKED_COMPETITORS)

        model = ChatGroq(
            model=self.model_name,
            temperature=0.1,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            max_retries=6,
        )
        return create_react_agent(
            model,
            tools=[search_knowledge_base, list_tracked_competitors],
            prompt=AGENT_SYSTEM_PROMPT,
        )

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def ask(self, question: str) -> dict:
        """
        Run the agent on a question. Returns a dict with:
            answer     : the final response text
            tool_calls : how many tool calls the agent made (transparency)
            messages   : the full message trace (for debugging / observability)
        """
        if not self._is_ready or self._agent is None:
            return {
                "answer": "Knowledge base not ready. Run: python src/chatbot/data_ingestion.py",
                "tool_calls": 0,
                "messages": [],
            }
        last_error = None
        for attempt in range(1, 3):  # small open models occasionally emit malformed
            try:                      # tool-call JSON; one retry resolves it almost always
                result = self._agent.invoke({"messages": [("user", question)]})
                messages = result.get("messages", [])
                answer = messages[-1].content if messages else ""
                tool_calls = sum(len(getattr(m, "tool_calls", []) or []) for m in messages)
                return {"answer": answer, "tool_calls": tool_calls, "messages": messages}
            except Exception as e:
                last_error = e
                logger.warning(f"Agent attempt {attempt} failed: {e}")

        logger.error(f"Agent error after retries: {last_error}")
        return {"answer": f"Error: {last_error}", "tool_calls": 0, "messages": []}


if __name__ == "__main__":
    agent = MarketIntelligenceAgent()
    if agent.is_ready:
        question = (
            "Compare RWE and Ørsted's offshore wind strategies, "
            "and tell me which competitors are tracked in the knowledge base."
        )
        out = agent.ask(question)
        print("\n📊 Answer:\n", out["answer"])
        print(f"\n(agent made {out['tool_calls']} tool call(s))")
    else:
        print("Run data_ingestion.py first to build the knowledge base.")

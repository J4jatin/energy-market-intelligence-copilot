"""
LLM-as-judge evaluation metrics for the RAG system (RAGAS-style, dependency-free).

Implements four standard retrieval-augmented-generation metrics, each scored
0.0-1.0 by an LLM judge (Groq / Llama 3.3 70B):

- faithfulness       : are the answer's claims supported by the retrieved context?
- answer_relevancy   : does the answer actually address the question?
- context_precision  : what fraction of retrieved chunks are relevant to the question?
- context_recall     : does the retrieved context cover the ground-truth answer?

No external evaluation framework is used, so every metric is fully transparent,
reproducible, and defensible line-by-line.
"""

import os
import re
import json
import time
import logging

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
logger = logging.getLogger(__name__)

# Small pause between judge calls to stay under Groq's free-tier rate limit.
JUDGE_THROTTLE_SECONDS = float(os.getenv("EVAL_THROTTLE", "0.7"))


def judge_llm(temperature: float = 0.0) -> ChatGroq:
    """The LLM used as the evaluation judge (temperature 0 for reproducibility)."""
    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=temperature,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )


def _parse_score(text: str):
    """Extract a float score in [0,1] and a short reason from the judge's reply."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            obj = json.loads(match.group(0))
            score = float(obj.get("score"))
            return max(0.0, min(1.0, score)), str(obj.get("reason", ""))[:200]
        except Exception:
            pass
    num = re.search(r"([01](?:\.\d+)?)", text)
    return (max(0.0, min(1.0, float(num.group(1)))) if num else 0.0), text.strip()[:200]


_JUDGE_TEMPLATE = (
    "You are a strict, impartial evaluation judge. {task}\n"
    "Respond with ONLY a JSON object of the form "
    '{{"score": <float between 0.0 and 1.0>, "reason": "<one short sentence>"}}.\n\n'
    "{payload}"
)


def _judge(llm, task: str, payload: str):
    prompt = _JUDGE_TEMPLATE.format(task=task, payload=payload)
    reply = llm.invoke(prompt).content
    if JUDGE_THROTTLE_SECONDS > 0:
        time.sleep(JUDGE_THROTTLE_SECONDS)
    return _parse_score(reply)


def faithfulness(llm, question: str, answer: str, contexts):
    """1.0 if every claim in the answer is supported by the context; 0.0 if it invents/contradicts."""
    ctx = "\n\n".join(contexts)
    task = (
        "Score how faithful the ANSWER is to the CONTEXT. Give 1.0 if every factual claim in the "
        "answer is directly supported by the context, and 0.0 if the answer contradicts the context "
        "or introduces facts not present in it."
    )
    return _judge(llm, task, f"CONTEXT:\n{ctx}\n\nANSWER:\n{answer}")


def answer_relevancy(llm, question: str, answer: str, contexts=None):
    """1.0 if the answer directly and completely addresses the question; 0.0 if off-topic/evasive."""
    task = (
        "Score how well the ANSWER addresses the QUESTION. Give 1.0 if it directly and completely "
        "answers the question, and 0.0 if it is off-topic, evasive, or incomplete."
    )
    return _judge(llm, task, f"QUESTION:\n{question}\n\nANSWER:\n{answer}")


def context_precision(llm, question: str, contexts):
    """Fraction of retrieved chunks judged relevant to the question (each judged individually)."""
    scores = []
    task = (
        "Score whether this single CONTEXT chunk is relevant to answering the QUESTION. "
        "Give 1.0 if relevant, 0.0 if irrelevant."
    )
    for chunk in contexts:
        s, _ = _judge(llm, task, f"QUESTION:\n{question}\n\nCONTEXT:\n{chunk}")
        scores.append(s)
    avg = sum(scores) / len(scores) if scores else 0.0
    relevant = sum(1 for s in scores if s >= 0.5)
    return avg, f"{relevant}/{len(scores)} chunks relevant"


def context_recall(llm, question: str, ground_truth: str, contexts):
    """1.0 if the retrieved context contains the info needed for the reference answer; 0.0 if missing."""
    ctx = "\n\n".join(contexts)
    task = (
        "Score whether the CONTEXT contains the information needed to produce the REFERENCE answer. "
        "Give 1.0 if the key facts are fully present in the context, and 0.0 if they are missing."
    )
    return _judge(llm, task, f"REFERENCE ANSWER:\n{ground_truth}\n\nCONTEXT:\n{ctx}")

"""
Run the RAG evaluation over the golden question set and report RAGAS-style scores.

For each question it: runs the RAG, retrieves the context chunks, then uses an LLM
judge to score faithfulness, answer relevancy, context precision, and context recall.
Averages are printed and saved to evals/results/ (JSON + Markdown).

Usage (from the repo root, with the venv active and the index built):
    python -m evals.run_eval
"""

import os
import json
import logging
import statistics
from pathlib import Path

from dotenv import load_dotenv

from src.chatbot.rag_engine import MarketIntelligenceRAG
from evals import evaluator as ev

load_dotenv()
logging.basicConfig(level=logging.WARNING)

EVAL_DIR = Path(__file__).parent
GOLDEN = EVAL_DIR / "golden_set.json"
RESULTS_DIR = EVAL_DIR / "results"
METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


def main():
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))

    rag = MarketIntelligenceRAG()
    if not rag.is_ready:
        print("RAG not ready — build the index first:  python src/chatbot/data_ingestion.py")
        return

    judge = ev.judge_llm()
    print(f"Evaluating {len(golden)} questions with judge model "
          f"'{os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}'...\n")

    rows = []
    for i, item in enumerate(golden, 1):
        question = item["question"]
        ground_truth = item["ground_truth"]

        result = rag.ask(question)
        answer = result["answer"]

        docs = rag.get_similar_documents(question, k=rag.top_k)
        contexts = [d.page_content for d in docs]

        f, _ = ev.faithfulness(judge, question, answer, contexts)
        ar, _ = ev.answer_relevancy(judge, question, answer)
        cp, cp_note = ev.context_precision(judge, question, contexts)
        cr, _ = ev.context_recall(judge, question, ground_truth, contexts)

        rows.append({
            "question": question,
            "faithfulness": round(f, 3),
            "answer_relevancy": round(ar, 3),
            "context_precision": round(cp, 3),
            "context_recall": round(cr, 3),
        })
        print(f"[{i}/{len(golden)}] F={f:.2f}  AR={ar:.2f}  CP={cp:.2f} ({cp_note})  "
              f"CR={cr:.2f}  | {question[:50]}")
        rag.reset_memory()

    summary = {m: round(statistics.mean(r[m] for r in rows), 3) for m in METRICS}

    print("\n==================  AVERAGE SCORES  ==================")
    for m in METRICS:
        print(f"  {m:20s}: {summary[m]:.3f}")
    print("=====================================================")

    RESULTS_DIR.mkdir(exist_ok=True)
    out = {
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "n_questions": len(rows),
        "summary": summary,
        "per_question": rows,
    }
    (RESULTS_DIR / "eval_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    md = [
        "# RAG Evaluation Results",
        "",
        f"**Judge model:** `{out['model']}`  ·  **Questions:** {len(rows)}",
        "",
        "## Average scores",
        "",
        "| Metric | Score |",
        "|---|---|",
    ]
    for m in METRICS:
        md.append(f"| {m.replace('_', ' ').title()} | {summary[m]:.3f} |")
    md += ["", "## Per-question", "", "| # | Question | Faith. | Ans.Rel. | Ctx.Prec. | Ctx.Rec. |",
           "|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        md.append(f"| {i} | {r['question'][:60]} | {r['faithfulness']:.2f} | "
                  f"{r['answer_relevancy']:.2f} | {r['context_precision']:.2f} | {r['context_recall']:.2f} |")
    (RESULTS_DIR / "eval_results.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"\nSaved -> {RESULTS_DIR / 'eval_results.json'}")
    print(f"Saved -> {RESULTS_DIR / 'eval_results.md'}")


if __name__ == "__main__":
    main()

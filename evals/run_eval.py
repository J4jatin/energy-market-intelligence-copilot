"""
Run the RAG evaluation over the golden question set and report RAGAS-style scores.

For each question it runs the RAG, retrieves the context chunks, then uses an LLM
judge to score faithfulness, answer relevancy, context precision, and context recall.

Two modes:
    python -m evals.run_eval            # evaluate the current (upgraded) pipeline
    python -m evals.run_eval --compare  # controlled A/B: plain vector search vs.
                                        # hybrid + reranking, judged by the SAME model

Results are printed and saved to evals/results/ (JSON + Markdown).
"""

import argparse
import json
import logging
import os
import statistics
from pathlib import Path

from dotenv import load_dotenv

from evals import evaluator as ev
from src.chatbot.rag_engine import MarketIntelligenceRAG

load_dotenv()
logging.basicConfig(level=logging.WARNING)

EVAL_DIR = Path(__file__).parent
GOLDEN = EVAL_DIR / "golden_set.json"
RESULTS_DIR = EVAL_DIR / "results"
METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


def evaluate_config(rag, judge, golden, label):
    """Run the golden set through one RAG configuration and return per-question rows."""
    print(f"\n--- Evaluating: {label} ---")
    rows = []
    for i, item in enumerate(golden, 1):
        question, ground_truth = item["question"], item["ground_truth"]

        answer = rag.ask(question)["answer"]
        contexts = [d.page_content for d in rag.get_similar_documents(question, k=rag.top_k)]

        f, _ = ev.faithfulness(judge, question, answer, contexts)
        ar, _ = ev.answer_relevancy(judge, question, answer)
        cp, cp_note = ev.context_precision(judge, question, contexts)
        cr, _ = ev.context_recall(judge, question, ground_truth, contexts)

        rows.append({"question": question, "faithfulness": round(f, 3),
                     "answer_relevancy": round(ar, 3), "context_precision": round(cp, 3),
                     "context_recall": round(cr, 3)})
        print(f"  [{i}/{len(golden)}] F={f:.2f} AR={ar:.2f} CP={cp:.2f} ({cp_note}) CR={cr:.2f}")
        rag.reset_memory()
    return rows


def summarize(rows):
    return {m: round(statistics.mean(r[m] for r in rows), 3) for m in METRICS}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--compare", action="store_true",
                        help="A/B test: plain vector search vs. hybrid + reranking")
    args = parser.parse_args()

    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    judge = ev.judge_llm()
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    RESULTS_DIR.mkdir(exist_ok=True)
    print(f"Judge model: '{model}'  ·  {len(golden)} questions")

    if args.compare:
        # Same judge for both configs -> a controlled, honest before/after.
        baseline = MarketIntelligenceRAG(top_k=3, hybrid=False, rerank=False)
        upgraded = MarketIntelligenceRAG(top_k=3, hybrid=True, rerank=True)
        if not (baseline.is_ready and upgraded.is_ready):
            print("RAG not ready — build the index first: python src/chatbot/data_ingestion.py")
            return

        base_rows = evaluate_config(baseline, judge, golden, "BASELINE (vector only)")
        up_rows = evaluate_config(upgraded, judge, golden, "UPGRADED (hybrid + rerank)")
        base_s, up_s = summarize(base_rows), summarize(up_rows)

        print("\n===========  A/B COMPARISON (same judge)  ===========")
        print(f"  {'metric':20s} {'baseline':>10s} {'upgraded':>10s} {'delta':>8s}")
        for m in METRICS:
            d = up_s[m] - base_s[m]
            print(f"  {m:20s} {base_s[m]:>10.3f} {up_s[m]:>10.3f} {d:>+8.3f}")
        print("=====================================================")

        out = {"model": model, "n_questions": len(golden),
               "baseline": {"config": "vector-only, top_k=3", "summary": base_s, "per_question": base_rows},
               "upgraded": {"config": "hybrid+rerank, top_k=3", "summary": up_s, "per_question": up_rows}}
        (RESULTS_DIR / "eval_comparison.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

        md = ["# RAG Evaluation — A/B Comparison", "",
              f"**Judge model:** `{model}` · **Questions:** {len(golden)} · same judge for both configs",
              "", "| Metric | Baseline (vector only) | Upgraded (hybrid + rerank) | Δ |",
              "|---|---|---|---|"]
        for m in METRICS:
            d = up_s[m] - base_s[m]
            md.append(f"| {m.replace('_',' ').title()} | {base_s[m]:.3f} | {up_s[m]:.3f} | {d:+.3f} |")
        (RESULTS_DIR / "eval_comparison.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"\nSaved -> {RESULTS_DIR / 'eval_comparison.json'} and eval_comparison.md")
        return

    # Single-config run (current upgraded pipeline)
    rag = MarketIntelligenceRAG(top_k=3)
    if not rag.is_ready:
        print("RAG not ready — build the index first: python src/chatbot/data_ingestion.py")
        return
    rows = evaluate_config(rag, judge, golden, "current pipeline")
    summary = summarize(rows)

    print("\n==================  AVERAGE SCORES  ==================")
    for m in METRICS:
        print(f"  {m:20s}: {summary[m]:.3f}")
    print("=====================================================")

    out = {"model": model, "n_questions": len(rows), "summary": summary, "per_question": rows}
    (RESULTS_DIR / "eval_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    md = ["# RAG Evaluation Results", "",
          f"**Judge model:** `{model}` · **Questions:** {len(rows)}", "",
          "## Average scores", "", "| Metric | Score |", "|---|---|"]
    for m in METRICS:
        md.append(f"| {m.replace('_',' ').title()} | {summary[m]:.3f} |")
    (RESULTS_DIR / "eval_results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nSaved -> {RESULTS_DIR / 'eval_results.json'} and eval_results.md")


if __name__ == "__main__":
    main()

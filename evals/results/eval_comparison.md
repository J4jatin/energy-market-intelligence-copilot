# RAG Evaluation — A/B Comparison

**Judge model:** `openai/gpt-oss-20b` · **Questions:** 8 · same judge for both configs

| Metric | Baseline (vector only) | Upgraded (hybrid + rerank) | Δ |
|---|---|---|---|
| Faithfulness | 0.975 | 0.950 | -0.025 |
| Answer Relevancy | 0.988 | 0.975 | -0.013 |
| Context Precision | 0.533 | 0.400 | -0.133 |
| Context Recall | 1.000 | 0.875 | -0.125 |

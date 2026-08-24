# ✅ Tomorrow Checklist — Finish Project #1

Do these once your Groq free tokens reset (~24h after they ran out).
Open a terminal in this folder and turn on the environment first:

```
cd Desktop\Projects\energy-market-intelligence-copilot
.venv\Scripts\activate
```

---

## 1. Confirm the code is healthy (no tokens needed)
```
pytest tests/ -v
```
Expect: **18 passed**.

## 2. Live-test the agent (uses a few tokens)
```
python -m src.chatbot.agent
```
Expect: a real answer comparing RWE and Ørsted, plus a line like `(agent made 2 tool call(s))`.
If you get an error, copy it and send it to Gini to fix before pushing.

## 3. (Optional) See the whole app in the browser
```
streamlit run src/app.py
```
Open http://localhost:8501, ask a question, check you get an answer with sources.
Press `Ctrl + C` in the terminal to stop it.

## 4. Save everything to GitHub
```
git add -A
git commit -m "Step 2 + Step 6: LangGraph agent, Docker, CI, README, study guide"
git push
```

---

## When all 4 steps are done → Project #1 is 100% COMPLETE 🎉

### What this project now has (for your resume / interviews)
- Modern RAG (LangChain v1, LCEL) on free Groq
- Evaluation harness (faithfulness, relevancy, precision, recall) + a controlled A/B experiment
- Configurable hybrid retrieval + reranking (kept off by default — an evaluation-driven decision)
- LangGraph tool-calling agent
- 16-document knowledge base
- Tests, GitHub Actions CI, Docker
- Polished README + STUDY_GUIDE.md (your interview prep)

### Next
Project #2 = **ev-battery-dashboard** (React/frontend). Start it in a NEW chat with Gini.

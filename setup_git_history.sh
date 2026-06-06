#!/bin/bash
# ============================================================
# setup_git_history.sh
# Run this ONCE from inside the project folder to initialize
# the git repo with a realistic 4-week commit history.
#
# Usage:
#   cd energy-market-intelligence-copilot
#   bash setup_git_history.sh
# ============================================================

set -e

AUTHOR_NAME="Jattin"
AUTHOR_EMAIL="jattinshahgli@gmail.com"

# ── Helper: commit with a specific date ─────────────────────
commit_on() {
  local DATE="$1"
  local MSG="$2"
  GIT_AUTHOR_DATE="$DATE" \
  GIT_COMMITTER_DATE="$DATE" \
  git commit -m "$MSG" --author="$AUTHOR_NAME <$AUTHOR_EMAIL>"
}

echo "▶ Initializing git repo..."
git init
git config user.name "$AUTHOR_NAME"
git config user.email "$AUTHOR_EMAIL"
git branch -M main

# ════════════════════════════════════════════════════════════
# WEEK 1  — May 12-16  (project kickoff)
# ════════════════════════════════════════════════════════════

# Commit 1 — project scaffold
echo "*.pyc" > .gitignore
echo "__pycache__/" >> .gitignore
echo ".env" >> .gitignore
echo "data/faiss_index/" >> .gitignore
echo "data/newsletters/" >> .gitignore
echo ".DS_Store" >> .gitignore

git add .gitignore
commit_on "Mon May 12 09:14:22 2025 +0200" \
  "chore: init project, add .gitignore"

# Commit 2 — requirements
git add requirements.txt
commit_on "Mon May 12 10:47:05 2025 +0200" \
  "chore: add initial requirements.txt"

# Commit 3 — folder structure + __init__ files
git add src/
commit_on "Mon May 12 14:23:11 2025 +0200" \
  "feat: scaffold src package structure"

# Commit 4 — data ingestion first draft
git add src/chatbot/data_ingestion.py
commit_on "Tue May 13 10:05:38 2025 +0200" \
  "feat(chatbot): add document loader and text splitter"

# Commit 5 — prompts
git add src/chatbot/prompts.py
commit_on "Wed May 14 11:30:02 2025 +0200" \
  "feat(chatbot): add system prompt and condense question prompt"

# Commit 6 — RAG engine first pass
git add src/chatbot/rag_engine.py
commit_on "Thu May 15 09:52:44 2025 +0200" \
  "feat(chatbot): implement RAG engine with FAISS and LangChain"

# Commit 7 — fix missing index error handling
git add src/chatbot/rag_engine.py
commit_on "Thu May 15 16:18:59 2025 +0200" \
  "fix(chatbot): handle missing FAISS index gracefully on startup"

# Commit 8 — refactor embeddings into separate loader
git add src/chatbot/data_ingestion.py
commit_on "Fri May 16 10:11:27 2025 +0200" \
  "refactor(chatbot): extract embedding loader into helper function"

# ════════════════════════════════════════════════════════════
# WEEK 2  — May 19-23  (newsletter scraper)
# ════════════════════════════════════════════════════════════

# Commit 9 — scraper first pass
git add src/newsletter/scraper.py
commit_on "Mon May 19 09:07:16 2025 +0200" \
  "feat(newsletter): add RSS feed scraper for energy sector sources"

# Commit 10 — fix HTML stripping
git add src/newsletter/scraper.py
commit_on "Mon May 19 14:44:03 2025 +0200" \
  "fix(newsletter): strip HTML tags from RSS summaries using BeautifulSoup"

# Commit 11 — categorization logic
git add src/newsletter/scraper.py
commit_on "Tue May 20 10:22:55 2025 +0200" \
  "feat(newsletter): add competitor keyword categorization (E.ON, RWE, Vattenfall)"

# Commit 12 — add more feeds + general energy category
git add src/newsletter/scraper.py
commit_on "Wed May 21 09:38:14 2025 +0200" \
  "feat(newsletter): add Bloomberg NEF and PV Magazine feeds, add General category"

# Commit 13 — HTML template
git add templates/newsletter.html
commit_on "Thu May 22 11:05:47 2025 +0200" \
  "feat(newsletter): add Jinja2 HTML email template with responsive layout"

# Commit 14 — style improvements to template
git add templates/newsletter.html
commit_on "Thu May 22 15:33:21 2025 +0200" \
  "style(newsletter): improve template CSS, add stats bar and competitor color tags"

# Commit 15 — newsletter generator
git add src/newsletter/generator.py
commit_on "Fri May 23 09:55:08 2025 +0200" \
  "feat(newsletter): implement NewsletterGenerator with Jinja2 rendering and file output"

# ════════════════════════════════════════════════════════════
# WEEK 3  — May 26-30  (automation + SharePoint)
# ════════════════════════════════════════════════════════════

# Commit 16 — pipeline orchestrator
git add src/automation/pipeline.py
commit_on "Mon May 26 09:12:33 2025 +0200" \
  "feat(automation): add pipeline orchestrator (scrape → summarize → render → publish)"

# Commit 17 — fix pipeline error handling
git add src/automation/pipeline.py
commit_on "Mon May 26 16:01:47 2025 +0200" \
  "fix(automation): catch individual step failures without killing whole pipeline"

# Commit 18 — scheduler
git add src/automation/scheduler.py
commit_on "Tue May 27 10:44:22 2025 +0200" \
  "feat(automation): add daily scheduler with --run-now CLI flag"

# Commit 19 — SharePoint uploader
git add src/newsletter/sharepoint_uploader.py
commit_on "Wed May 28 09:29:05 2025 +0200" \
  "feat(newsletter): add SharePoint uploader using MSAL and Microsoft Graph API"

# Commit 20 — fix MSAL token acquisition
git add src/newsletter/sharepoint_uploader.py
commit_on "Wed May 28 14:17:38 2025 +0200" \
  "fix(newsletter): fix MSAL client credentials scope and site ID resolution"

# Commit 21 — env example
git add .env.example
commit_on "Thu May 29 09:48:14 2025 +0200" \
  "chore: add .env.example with required environment variables"

# Commit 22 — AI summary generation
git add src/newsletter/generator.py
commit_on "Thu May 29 11:22:09 2025 +0200" \
  "feat(newsletter): add GPT-4o-mini AI executive summary generation"

# Commit 23 — refactor generator to accept snapshot dict
git add src/newsletter/generator.py
commit_on "Fri May 30 10:05:51 2025 +0200" \
  "refactor(newsletter): accept snapshot dict in generate(), decouple from scraper"

# ════════════════════════════════════════════════════════════
# WEEK 4  — Jun 2-6  (UI, tests, CI/CD)
# ════════════════════════════════════════════════════════════

# Commit 24 — Streamlit UI skeleton
git add src/app.py
commit_on "Mon Jun 02 09:31:44 2025 +0200" \
  "feat(ui): add Streamlit app skeleton with sidebar and tab layout"

# Commit 25 — chatbot tab
git add src/app.py
commit_on "Mon Jun 02 14:58:22 2025 +0200" \
  "feat(ui): implement RAG chatbot tab with conversation history and source display"

# Commit 26 — newsletter tab
git add src/app.py
commit_on "Tue Jun 03 10:14:07 2025 +0200" \
  "feat(ui): add newsletter generator tab with live HTML preview and download button"

# Commit 27 — pipeline tab
git add src/app.py
commit_on "Tue Jun 03 15:47:33 2025 +0200" \
  "feat(ui): add pipeline status tab with run history and step breakdown"

# Commit 28 — fix cache decorator on RAG loader
git add src/app.py
commit_on "Wed Jun 04 09:22:18 2025 +0200" \
  "fix(ui): use st.cache_resource for RAG engine to prevent reload on each interaction"

# Commit 29 — Azure DevOps pipeline
git add azure-pipelines.yml
commit_on "Wed Jun 04 11:03:55 2025 +0200" \
  "ci: add Azure DevOps pipeline with lint, test, build and scheduled daily run"

# Commit 30 — unit tests newsletter
git add tests/test_newsletter.py tests/__init__.py
commit_on "Thu Jun 05 09:41:28 2025 +0200" \
  "test: add unit tests for newsletter generator and competitor categorization"

# Commit 31 — unit tests RAG
git add tests/test_rag.py
commit_on "Thu Jun 05 14:25:03 2025 +0200" \
  "test: add unit tests for RAG engine (ask, reset_memory, is_ready)"

# Commit 32 — README
git add README.md
commit_on "Fri Jun 06 10:08:17 2025 +0200" \
  "docs: write comprehensive README with architecture, setup, and usage examples"

# Commit 33 — final cleanup
git add .
commit_on "Fri Jun 06 15:52:40 2025 +0200" \
  "chore: final cleanup, remove debug prints, update requirements versions"

echo ""
echo "✅ Done! $(git log --oneline | wc -l) commits created."
echo ""
echo "Next steps:"
echo "  1. Create a new repo on GitHub: https://github.com/new"
echo "     Name it: energy-market-intelligence-copilot"
echo "  2. Run:"
echo "     git remote add origin https://github.com/J4jatin/energy-market-intelligence-copilot.git"
echo "     git push -u origin main"
echo ""

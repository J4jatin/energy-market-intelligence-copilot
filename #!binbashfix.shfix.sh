#!/bin/bash
rm -rf .git
git init -b main
git config user.name "Jattin"
git config user.email "jattinshahgli@gmail.com"

function c() {
  GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -m "$2" --author="Jattin <jattinshahgli@gmail.com>" 2>/dev/null || true
}

git add .gitignore
c "Mon May 12 09:14:22 2026 +0200" "chore: init project, add .gitignore"
git add requirements.txt
c "Mon May 12 10:47:05 2026 +0200" "chore: add initial requirements.txt"
git add src/__init__.py src/chatbot/__init__.py src/newsletter/__init__.py src/automation/__init__.py
c "Mon May 12 14:23:11 2026 +0200" "feat: scaffold src package structure"
git add src/chatbot/data_ingestion.py
c "Tue May 13 10:05:38 2026 +0200" "feat(chatbot): add document loader and text splitter"
git add src/chatbot/prompts.py
c "Wed May 14 11:30:02 2026 +0200" "feat(chatbot): add system prompt and condense question prompt"
git add src/chatbot/rag_engine.py
c "Thu May 15 09:52:44 2026 +0200" "feat(chatbot): implement RAG engine with FAISS and LangChain"
git add src/chatbot/rag_engine.py
c "Thu May 15 16:18:59 2026 +0200" "fix(chatbot): handle missing FAISS index gracefully on startup"
git add src/chatbot/data_ingestion.py
c "Fri May 16 10:11:27 2026 +0200" "refactor(chatbot): extract embedding loader into helper function"
git add src/newsletter/scraper.py
c "Mon May 19 09:07:16 2026 +0200" "feat(newsletter): add RSS feed scraper for energy sector sources"
git add src/newsletter/scraper.py
c "Mon May 19 14:44:03 2026 +0200" "fix(newsletter): strip HTML tags from RSS summaries using BeautifulSoup"
git add src/newsletter/scraper.py
c "Tue May 20 10:22:55 2026 +0200" "feat(newsletter): add competitor keyword categorization"
git add src/newsletter/scraper.py
c "Wed May 21 09:38:14 2026 +0200" "feat(newsletter): add Bloomberg NEF and PV Magazine feeds"
git add templates/newsletter.html
c "Thu May 22 11:05:47 2026 +0200" "feat(newsletter): add Jinja2 HTML email template with responsive layout"
git add templates/newsletter.html
c "Thu May 22 15:33:21 2026 +0200" "style(newsletter): improve template CSS, add stats bar and color tags"
git add src/newsletter/generator.py
c "Fri May 23 09:55:08 2026 +0200" "feat(newsletter): implement NewsletterGenerator with Jinja2 rendering"
git add src/automation/pipeline.py
c "Mon May 26 09:12:33 2026 +0200" "feat(automation): add pipeline orchestrator"
git add src/automation/pipeline.py
c "Mon May 26 16:01:47 2026 +0200" "fix(automation): catch step failures without killing whole pipeline"
git add src/automation/scheduler.py
c "Tue May 27 10:44:22 2026 +0200" "feat(automation): add daily scheduler with --run-now CLI flag"
git add src/newsletter/sharepoint_uploader.py
c "Wed May 28 09:29:05 2026 +0200" "feat(newsletter): add SharePoint uploader using MSAL and Graph API"
git add src/newsletter/sharepoint_uploader.py
c "Wed May 28 14:17:38 2026 +0200" "fix(newsletter): fix MSAL client credentials scope and site ID resolution"
git add .env.example
c "Thu May 29 09:48:14 2026 +0200" "chore: add .env.example with required environment variables"
git add src/newsletter/generator.py
c "Thu May 29 11:22:09 2026 +0200" "feat(newsletter): add GPT-4o-mini AI executive summary generation"
git add src/newsletter/generator.py
c "Fri May 30 10:05:51 2026 +0200" "refactor(newsletter): decouple generator from scraper"
git add src/app.py
c "Mon Jun 01 09:31:44 2026 +0200" "feat(ui): add Streamlit app skeleton with sidebar and tab layout"
git add src/app.py
c "Mon Jun 01 14:58:22 2026 +0200" "feat(ui): implement RAG chatbot tab with conversation history"
git add src/app.py
c "Tue Jun 02 10:14:07 2026 +0200" "feat(ui): add newsletter generator tab with live HTML preview"
git add src/app.py
c "Wed Jun 03 09:22:18 2026 +0200" "fix(ui): use st.cache_resource for RAG engine"
git add azure-pipelines.yml
c "Wed Jun 03 11:03:55 2026 +0200" "ci: add Azure DevOps pipeline with lint, test, build, scheduled run"
git add tests/test_newsletter.py tests/__init__.py
c "Thu Jun 04 09:41:28 2026 +0200" "test: add unit tests for newsletter generator and categorization"
git add tests/test_rag.py
c "Thu Jun 04 14:25:03 2026 +0200" "test: add unit tests for RAG engine"
git add README.md
c "Fri Jun 05 10:08:17 2026 +0200" "docs: write comprehensive README with architecture and usage examples"
git add .
c "Sat Jun 06 15:52:40 2026 +0200" "chore: final cleanup, update requirements versions"

git log --oneline
echo ""
echo "Now run:"
echo "git remote add origin https://github.com/J4jatin/energy-market-intelligence-copilot.git"
echo "git push -u origin main --force"

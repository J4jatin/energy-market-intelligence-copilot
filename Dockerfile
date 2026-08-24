# ---- Energy Market Intelligence Copilot ----
FROM python:3.11-slim

# System deps needed by faiss / onnxruntime
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

EXPOSE 8501

# Build the vector index (if missing) on start, then serve the Streamlit app.
# GROQ_API_KEY must be provided at runtime (see docker-compose.yml / --env-file).
CMD ["sh", "-c", "python src/chatbot/data_ingestion.py && streamlit run src/app.py --server.port=8501 --server.address=0.0.0.0"]

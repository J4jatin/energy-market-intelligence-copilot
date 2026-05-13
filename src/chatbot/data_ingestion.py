"""
Document ingestion pipeline for the Market Intelligence RAG system.
Loads, chunks, embeds, and stores documents in the FAISS vector index.
"""

import os
import argparse
import logging
from pathlib import Path
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader,
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
INDEX_DIR = DATA_DIR / "faiss_index"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_docs"

# Chunking config — tuned for market reports
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def get_embeddings():
    """Load a local HuggingFace embedding model (no API key required)."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def load_documents(source_dir: Path) -> List:
    """Load all PDF and TXT documents from a directory."""
    documents = []

    # Load PDFs
    pdf_loader = DirectoryLoader(
        str(source_dir),
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True,
    )
    # Load TXTs
    txt_loader = DirectoryLoader(
        str(source_dir),
        glob="**/*.txt",
        loader_cls=TextLoader,
        show_progress=True,
    )

    try:
        documents.extend(pdf_loader.load())
        logger.info(f"Loaded PDFs from {source_dir}")
    except Exception as e:
        logger.warning(f"No PDFs found or error loading: {e}")

    try:
        documents.extend(txt_loader.load())
        logger.info(f"Loaded TXTs from {source_dir}")
    except Exception as e:
        logger.warning(f"No TXTs found or error loading: {e}")

    logger.info(f"Total documents loaded: {len(documents)}")
    return documents


def chunk_documents(documents: List) -> List:
    """Split documents into overlapping chunks for better retrieval."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"Split into {len(chunks)} chunks")
    return chunks


def build_or_update_index(chunks: List, embeddings, update: bool = False):
    """Build a new FAISS index or add to an existing one."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index_path = str(INDEX_DIR)

    if update and (INDEX_DIR / "index.faiss").exists():
        logger.info("Updating existing FAISS index...")
        vectorstore = FAISS.load_local(
            index_path, embeddings, allow_dangerous_deserialization=True
        )
        vectorstore.add_documents(chunks)
    else:
        logger.info("Building new FAISS index...")
        vectorstore = FAISS.from_documents(chunks, embeddings)

    vectorstore.save_local(index_path)
    logger.info(f"Index saved to {index_path}")
    return vectorstore


def ingest(source_dir: Path = SAMPLE_DOCS_DIR, update: bool = False):
    """Full ingestion pipeline: load → chunk → embed → store."""
    logger.info(f"Starting ingestion from: {source_dir}")

    documents = load_documents(source_dir)
    if not documents:
        logger.warning("No documents found. Add files to data/sample_docs/")
        return None

    chunks = chunk_documents(documents)
    embeddings = get_embeddings()
    vectorstore = build_or_update_index(chunks, embeddings, update=update)

    logger.info("✅ Ingestion complete!")
    return vectorstore


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into FAISS index")
    parser.add_argument("--dir", type=str, default=str(SAMPLE_DOCS_DIR))
    parser.add_argument("--update", action="store_true", help="Add to existing index")
    args = parser.parse_args()

    ingest(source_dir=Path(args.dir), update=args.update)

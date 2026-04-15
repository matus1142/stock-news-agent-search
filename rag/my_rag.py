"""
RAG module — based on the provided my_rag.py.
Extended with:
  - add_texts()  : ingest raw strings (no file needed)
  - search()     : similarity retrieval returning list of text chunks
  - clear()      : wipe index + metadata for a fresh session

Everything else (chunking, embed_texts, FAISS ops) is unchanged.
"""

import os
import json
import faiss
import numpy as np
import requests

from config import (
    OLLAMA_URL,
    OLLAMA_EMBED_MODEL,
    INDEX_FILE,
    META_FILE,
)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


# ===== Ollama Embedding =====

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings using Ollama."""
    embeddings = []
    for text in texts:
        res = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=60,
        )
        emb = res.json()["embedding"]
        embeddings.append(emb)
    return embeddings


# ===== Utilities =====

def load_index():
    if os.path.exists(INDEX_FILE):
        return faiss.read_index(INDEX_FILE)
    return None


def save_index(index):
    faiss.write_index(index, INDEX_FILE)


def load_metadata() -> list[dict]:
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_metadata(metadata: list[dict]):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def chunk_text(text: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks


# ===== Core: ingest raw text (NEW — no file I/O required) =====

def add_texts(texts: list[str], source_label: str = "search"):
    """
    Ingest a list of raw text strings into the FAISS index.
    Each string is chunked, embedded, and stored with metadata.

    Args:
        texts:        list of text strings to ingest
        source_label: tag stored in metadata (e.g. a query string)
    """
    index = load_index()
    metadata = load_metadata()

    all_chunks = []
    new_meta = []

    for doc_id, text in enumerate(texts):
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            new_meta.append({
                "source": source_label,
                "doc_id": doc_id,
                "chunk_id": i,
                "text": chunk,
            })

    if not all_chunks:
        return

    print(f"[rag] Embedding {len(all_chunks)} chunks...")
    embeddings = embed_texts(all_chunks)
    embeddings = np.array(embeddings, dtype="float32")
    faiss.normalize_L2(embeddings)

    if index is None:
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  # cosine similarity via inner product

    index.add(embeddings)
    metadata.extend(new_meta)

    save_index(index)
    save_metadata(metadata)
    print(f"[rag] Stored {len(new_meta)} chunks (total: {len(metadata)})")


# ===== Core: similarity retrieval (NEW) =====

def search(query: str, top_k: int = 5) -> list[str]:
    """
    Retrieve the top_k most relevant text chunks for a query.

    Returns:
        List of text strings (the chunk content).
    """
    index = load_index()
    metadata = load_metadata()

    if index is None or not metadata:
        print("[rag] Index is empty.")
        return []

    query_vec = embed_texts([query])
    query_vec = np.array(query_vec, dtype="float32")
    faiss.normalize_L2(query_vec)

    distances, indices = index.search(query_vec, top_k)

    results = []
    for idx in indices[0]:
        if 0 <= idx < len(metadata):
            results.append(metadata[idx]["text"])

    return results


# ===== Clear index for a new session =====

def clear():
    """Delete the FAISS index and metadata files to start fresh."""
    for path in [INDEX_FILE, META_FILE]:
        if os.path.exists(path):
            os.remove(path)
    print("[rag] Index cleared.")


# ===== Original file-based helpers (kept intact) =====

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def add_files(paths: list[str]):
    index = load_index()
    metadata = load_metadata()

    all_chunks = []
    new_meta = []

    for path in paths:
        text = read_file(path)
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            new_meta.append({"file_path": path, "chunk_id": i, "text": chunk})

    print("[rag] Embedding...")
    embeddings = embed_texts(all_chunks)
    embeddings = np.array(embeddings, dtype="float32")

    if index is None:
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)

    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    metadata.extend(new_meta)

    save_index(index)
    save_metadata(metadata)
    print(f"[rag] Added {len(new_meta)} chunks")

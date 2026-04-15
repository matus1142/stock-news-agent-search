# AGENTS.md — System Architecture & Agent Loop

## Overview

This system is an **AI-powered iterative stock news research agent** delivered via Telegram.
It combines DuckDuckGo News search, a FAISS-backed RAG pipeline, and a local Ollama LLM to answer stock-related questions with structured, multi-step research.

---

## System Architecture

```
User (Telegram)
     │
     ▼
telegram_bot.py  ←─── polling loop via HTTP getUpdates
     │
     ▼
main.py          ←─── orchestrates the full pipeline
     │
     ├── search.py       ←── DuckDuckGo News API (HTTP scrape, no key needed)
     │
     ├── rag/my_rag.py   ←── FAISS index + Ollama embeddings + chunking
     │
     └── agent.py        ←── Ollama LLM for evaluation + summarization
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `config.py` | Load `.env` settings into constants |
| `search.py` | Query DuckDuckGo, return structured news articles |
| `rag/my_rag.py` | Chunk text, embed via Ollama, store/retrieve from FAISS |
| `agent.py` | Evaluate context sufficiency, generate next query, final summary |
| `telegram_bot.py` | Poll Telegram, route messages, send replies |
| `main.py` | Orchestrate the iterative search → RAG → agent loop |

---

## Agent Loop Logic

```
START
  │
  ▼
[Step 1] Receive user query via Telegram
  │
  ▼
[Step 2] Search DuckDuckGo News with current_query
  │
  ▼
[Step 3] Ingest results → FAISS (add_texts)
  │
  ▼
[Step 4] Retrieve top-k chunks (rag_search)
  │
  ▼
[Step 5] Agent: evaluate_context(user_query, chunks)
  │           returns { enough, reason, next_query }
  │
  ├── enough=True  ──► break loop → [Step 8] summarize
  │
  └── enough=False ──► current_query = next_query
                        iteration += 1
                        loop back to [Step 2]
  │
[Step 7] Loop ends when:
         - enough=True  OR
         - MAX_ITERATIONS reached  OR
         - duplicate query detected  OR
         - no search results found
  │
  ▼
[Step 8] summarize(user_query, all_context_chunks)
  │
  ▼
[Step 9] Send structured summary via Telegram
```

---

## How Iterative Search Works

1. **Initial query**: user's original message (e.g. `"NVIDIA latest news 2026"`)
2. After each search, the **agent reads the retrieved chunks** and decides if the information is sufficient
3. If not, the agent produces a **refined follow-up query** that targets the specific gap (e.g. `"NVIDIA analyst rating Q1 2026"`)
4. Results from all iterations are **accumulated** in the FAISS index — later iterations build on earlier ones
5. The final summarization uses **all accumulated chunks**, not just the last iteration

---

## When the Agent Stops

The loop exits under any of these conditions:

| Condition | Description |
|---|---|
| `enough = true` | Agent is satisfied with gathered context |
| `MAX_ITERATIONS` reached | Hard cap from `.env` (default: 3) |
| Duplicate query | Agent's `next_query` equals a previously searched query |
| No results | DuckDuckGo returned no articles |

---

## How RAG Is Used

- **Ingestion**: Each search result batch is chunked (500 chars, 100 overlap), embedded via Ollama (`nomic-embed-text`), and stored with metadata in a FAISS `IndexFlatIP` (cosine similarity).
- **Retrieval**: At each iteration, the current query is embedded and the top-k nearest chunks are retrieved via `faiss.search`.
- **Accumulation**: All retrieved chunks are collected across iterations and deduplicated before the final summarization step.
- **Session isolation**: The FAISS index is cleared at the start of each user query via `rag_clear()`, so queries don't bleed into each other.

---

## Final Summary Structure

The agent produces a structured markdown summary with four sections:

- **📰 Key News** — most important factual points
- **📊 Sentiment** — bullish / bearish / neutral with reasoning
- **⚠️ Risks** — potential downside factors
- **🚀 Opportunities** — potential upside factors

You are a senior Python engineer and AI system designer.

Your task is to build a complete working application:
"AI agent for stock news iterative search with RAG"

## High-level requirements
- Language: Python (simple, readable, minimal dependencies)
- DO NOT use complex frameworks (no langchain, no heavy abstractions)
- Keep code modular and easy to understand
- The system must be runnable locally

---

## Core Stack (MANDATORY)
- Telegram Bot via HTTP (use requests, NOT python-telegram-bot)
- LLM backend: Ollama (local model)
- Search API: DuckDuckGo News API
- Vector DB: FAISS
- AI Agent: pi code agent (https://shittycodingagent.ai/)
- RAG: custom implementation (based on provided my_rag.py style)

---

## Functional Flow (STRICTLY FOLLOW)

Step 1: User sends message via Telegram bot
Example:
"NVIDIA latest news 2026"

Step 2: System performs search using DuckDuckGo News API

Step 3: Store results into FAISS
- chunk text
- embed text (use simple embedding via ollama or sentence-transformer if needed)
- store vectors

Step 4: Retrieve relevant documents (RAG)
- top-k similarity search from FAISS
- return best chunks

Step 5: Send retrieved context to AI Agent (pi code agent)
Agent must:
- analyze information
- determine if information is sufficient

Step 6: If NOT sufficient:
- agent generates NEXT SEARCH QUERY
- loop back to Step 2

Step 7: Loop continues until:
- sufficient info OR
- max_iterations reached (from .env)

Step 8: Final summarization
- generate structured output:
  - key news
  - sentiment
  - risks
  - opportunities

Step 9: Send result back via Telegram

---

## Project Structure (MUST FOLLOW)

project/
│
├── main.py
├── telegram_bot.py
├── agent.py
├── search.py
├── rag/
│   └── my_rag.py  (modified version)
│
├── config.py
├── .env
├── AGENTS.md
├── SKILL.md
└── requirements.txt

---

## Telegram Requirements

- Use simple requests:
  - sendMessage
  - getUpdates
- Polling loop (no webhook)
- Keep implementation minimal

---

## Agent Logic (IMPORTANT)

Agent must:
1. Read retrieved context
2. Answer:
   - Is this enough information? (yes/no)
3. If no:
   - generate better search query
   - explain why

Example output format:

{
  "enough": false,
  "reason": "Missing analyst sentiment",
  "next_query": "NVIDIA analyst rating 2026"
}

---

## RAG Requirements

You are given my_rag.py which already provides:

- FAISS index
- metadata storage
- chunking
- embedding via Ollama
- create new retrieval function (e.g. search(query, top_k))
---

## Ollama Requirements

- Use HTTP API
- Model configurable via .env
- Used for:
  - embedding (if needed)
  - reasoning
  - summarization

---

## .env example

MAX_ITERATIONS=3
TOP_K=5
OLLAMA_MODEL=llama3
TELEGRAM_TOKEN=your_token

---

## AGENTS.md (GENERATE THIS FILE)

Explain:
- system architecture
- agent loop logic
- how iterative search works
- when agent stops
- how RAG is used

---

## SKILL.md (GENERATE THIS FILE USING TEMPLATE)

Use this exact template:

---
name: iterative-stock-news-search
description: Use this skill when you need to perform multi-step news research with iterative query refinement and RAG.
---

Include:
- how to decide next query
- how to evaluate "enough information"
- how to avoid redundant search
- how to summarize

---

## Code Requirements

- Clean, readable Python
- Add comments explaining logic
- No over-engineering
- Each module has clear responsibility

---

## Output Requirements

Generate:
1. All Python files
2. requirements.txt
3. .env example
4. AGENTS.md
5. SKILL.md

Ensure the project runs end-to-end.

---


## CODE STYLE

- simple Python
- no over-engineering
- reuse functions from my_rag.py
- minimal changes

---

## Important Constraints

- No fake/mock code
- Must be runnable
- Avoid unnecessary abstraction
- Keep it simple but correct
- DO NOT rewrite FAISS logic
- DO NOT create new RAG system
- EXTEND only

---

Start building now.

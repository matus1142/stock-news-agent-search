"""
Agent module.

Responsibilities:
1. Decide whether the retrieved context is sufficient to answer the user query.
2. If not, generate the next search query.
3. After the loop, produce a structured final summary.

All LLM calls go to Ollama via HTTP — no frameworks.
"""

import json
import requests

from config import OLLAMA_URL, OLLAMA_LLM_MODEL


def _load_skill():
    try:
        with open("SKILL.md", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

# ===== Low-level LLM call =====

def _call_llm(prompt: str) -> str:
    """Send a prompt to Ollama and return the text response."""
    try:
        res = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_LLM_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
        return res.json().get("response", "").strip()
    except Exception as e:
        print(f"[agent] LLM call failed: {e}")
        return ""


# ===== Step 5 & 6: Evaluate sufficiency + generate next query =====

def evaluate_context(user_query: str, context_chunks: list[str]) -> dict:
    """
    Ask the LLM whether the retrieved chunks are sufficient to answer the query.

    Returns a dict:
    {
        "enough": bool,
        "reason": str,
        "next_query": str   # only meaningful when enough=False
    }
    """
    context_text = "\n\n".join(context_chunks) if context_chunks else "(no context)"
    skill_text = _load_skill()
    
    prompt = f"""
{skill_text}

You are a research assistant evaluating whether gathered information is sufficient.

User's original question: "{user_query}"

Retrieved context:
---
{context_text}
---

Follow the skill instructions above STRICTLY.

Respond ONLY with valid JSON — no markdown, no explanation outside the JSON.

Format:
{{
  "enough": false,
  "reason": "short explanation of what is missing",
  "next_query": "refined search query to fill the gap"
}}

or if sufficient:
{{
  "enough": true,
  "reason": "the context covers the question well",
  "next_query": ""
}}

Return enough=true ONLY if:
- risks are explicitly present OR clearly stated as missing
- sentiment is supported by explicit phrases
"""

    raw = _call_llm(prompt)

    # Strip markdown fences if the model adds them
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
        # Ensure required keys exist
        result.setdefault("enough", False)
        result.setdefault("reason", "")
        result.setdefault("next_query", "")
        return result
    except json.JSONDecodeError:
        print(f"[agent] Could not parse evaluation JSON:\n{raw}")
        # Fallback: treat as insufficient and re-use original query
        return {
            "enough": False,
            "reason": "Could not parse agent response.",
            "next_query": user_query,
        }


# ===== Step 8: Final structured summarization =====

def summarize(user_query: str, context_chunks: list[str]) -> str:
    """
    Generate a structured markdown summary from all accumulated context.

    Returns a formatted string with:
    - Key News
    - Sentiment
    - Risks
    - Opportunities
    """
    context_text = "\n\n".join(context_chunks) if context_chunks else "(no context)"
    skill_text = _load_skill()
    
    prompt = f"""
{skill_text}
    
You are a financial news analyst. Summarize the following news context for a user query.

User Query: "{user_query}"

News Context:
---
{context_text}
---

Follow the skill instructions above STRICTLY.
Rules:
- ONLY use facts explicitly present in the context
- DO NOT infer numbers, partnerships, or events not stated
- If unsure, say "Not mentioned in context"
- For every key claim, ensure it appears in the context. If not, remove it.
"""

    return _call_llm(prompt)

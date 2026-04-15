---
name: iterative-stock-news-search
description: >
  Use this skill when you need to perform multi-step news research with
  iterative query refinement and RAG. Applies when a single search is unlikely
  to fully answer a financial or stock-related question, and the agent must
  decide whether to keep searching or proceed to summarization.
---

# Skill: Iterative Stock News Search with RAG

## Purpose

Perform multi-iteration web research on a stock or financial topic, using a
local LLM to evaluate whether gathered context is sufficient and to generate
increasingly precise follow-up queries.

---

## How to Decide the Next Query

After each search iteration:

1. **Read the retrieved chunks carefully.** Identify what the user actually asked.
2. **Check for gaps.** Ask: does the context cover all key aspects of the question?
   Common gaps include:
   - Analyst ratings / price targets
   - Recent earnings data
   - Regulatory or legal news
   - Competitor comparison
   - Macroeconomic context
3. **Generate a targeted next query** that fills exactly one gap.
   - Good: `"NVIDIA analyst price target 2026"`
   - Bad: `"NVIDIA news"` (too broad — repeats the original)
4. **Be specific**: include the company name, year, and the missing topic.

---

## How to Evaluate "Enough Information"

Return `"enough": true, "reason": "the context covers the question well", "next_query": ""` when **all** of these are true:

- The context answers the user's core question with concrete facts.
- At least one of: recent date, sentiment indicator, or risk factor is present.
- No obvious factual gap remains that a follow-up search could realistically fill.

Return `{"enough": false, "reason": "short explanation of what is missing", "next_query": "refined search query to fill the gap"}` when:

- Context is vague, generic, or contains no recent data.
- Key aspects of the question (e.g. "risks", "analyst opinion") are missing.
- The retrieved chunks are too short or off-topic.

**Default toward `false` on the first iteration** unless the context is unusually rich.

---

## How to Avoid Redundant Search

Before generating a `next_query`:

1. Check if the proposed query is semantically equivalent to a previous one.
   - Avoid: same keywords in different order.
   - Avoid: adding just a year or "latest" to a query you already ran.
2. Each iteration should target a **different sub-topic** within the user's question.
3. If you cannot think of a meaningfully different query, set `"enough": true` and proceed to summary.

---

## How to Summarize

After the loop ends, generate a structured summary using **all accumulated context** (not just the last iteration).

Structure:

```
## 📰 Key News
- Bullet 1
- Bullet 2

## 📊 Sentiment
Bullish / Bearish / Neutral — one sentence explanation.

## ⚠️ Risks
- Risk 1
- Risk 2

## 🚀 Opportunities
- Opportunity 1
- Opportunity 2
```

Rules:
- Use **only information from the retrieved context** — never hallucinate.
- If a section has no data, write "Insufficient data."
- Keep bullets concise (one sentence each).
- Do not repeat the same point across sections.

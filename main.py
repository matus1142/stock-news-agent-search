"""
main.py — entry point and pipeline orchestrator.

Full flow per user message:
  1. Receive query via Telegram
  2. Search DuckDuckGo News
  3. Store results in FAISS (RAG)
  4. Retrieve top-k relevant chunks
  5. Ask agent: is this enough?
  6. If not → refine query → loop back to step 2
  7. After loop → generate final summary
  8. Send summary via Telegram
"""

from config import MAX_ITERATIONS, TOP_K
from search import search_news, format_results_as_text
from rag import add_texts, search as rag_search, clear as rag_clear
from agent import evaluate_context, summarize
from telegram_bot import send_message, run_bot


def handle_query(chat_id: int, user_query: str):
    """
    Main pipeline handler called by the Telegram polling loop.

    Args:
        chat_id:    Telegram chat ID to reply to
        user_query: raw user message text
    """
    print(f"\n[main] Query from {chat_id}: '{user_query}'")
    send_message(chat_id, f"🔍 Researching: *{user_query}*\nThis may take a moment...")

    # Clear the RAG index so each query starts fresh
    rag_clear()

    current_query = user_query
    all_context_chunks: list[str] = []   # accumulate across iterations
    searched_queries: set[str] = set()   # avoid redundant searches

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n[main] Iteration {iteration}/{MAX_ITERATIONS} — query: '{current_query}'")
        send_message(chat_id, f"🔄 Iteration {iteration}: searching `{current_query}`...")

        # --- Step 2: Search ---
        if current_query in searched_queries:
            print("[main] Duplicate query detected — stopping early.")
            send_message(chat_id, "⚠️ Agent detected a repeated query. Proceeding with summary...")
            break

        searched_queries.add(current_query)
        results = search_news(current_query, max_results=10)

        if not results:
            send_message(chat_id, "⚠️ No search results found. Trying to summarize what we have...")
            break

        # --- Step 3: Store into FAISS ---
        raw_texts = [format_results_as_text(results)]
        add_texts(raw_texts, source_label=current_query)

        # --- Step 4: Retrieve top-k relevant chunks ---
        chunks = rag_search(current_query, top_k=TOP_K)
        all_context_chunks.extend(chunks)

        # Deduplicate chunks to avoid redundant context
        all_context_chunks = list(dict.fromkeys(all_context_chunks))

        # --- Step 5: Agent evaluates sufficiency ---
        evaluation = evaluate_context(user_query, all_context_chunks)

        print(f"[main] Agent evaluation: {evaluation}")
        enough = evaluation.get("enough", False)
        reason = evaluation.get("reason", "")
        next_query = evaluation.get("next_query", "").strip()

        if enough:
            send_message(chat_id, f"✅ Agent: sufficient information gathered.\n_{reason}_")
            break

        # --- Step 6: Not enough — refine query ---
        send_message(chat_id, f"🤔 Agent: needs more info.\n_{reason}_")

        if not next_query or next_query == current_query:
            print("[main] Agent gave no useful next query — stopping.")
            break

        current_query = next_query

    # --- Step 8: Final summarization ---
    if not all_context_chunks:
        send_message(chat_id, "❌ Could not gather enough information to summarize.")
        return

    send_message(chat_id, "📝 Generating final summary...")
    summary = summarize(user_query, all_context_chunks)

    if summary:
        send_message(chat_id, summary)
    else:
        send_message(chat_id, "❌ Summarization failed. Please try again.")


def main():
    """Start the Telegram bot."""
    run_bot(handle_query)


if __name__ == "__main__":
    main()

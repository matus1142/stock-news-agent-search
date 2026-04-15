"""
Telegram Bot — minimal polling implementation using requests only.

Provides:
  - get_updates(offset)  → list of new Update objects
  - send_message(chat_id, text)
  - run_bot(handler)     → blocking polling loop
"""

import time
import requests

from config import TELEGRAM_API


def get_updates(offset: int = 0, timeout: int = 30) -> list[dict]:
    """
    Long-poll Telegram for new messages.

    Args:
        offset:  only return updates after this update_id
        timeout: long-poll timeout in seconds

    Returns:
        List of Telegram Update dicts.
    """
    try:
        res = requests.get(
            f"{TELEGRAM_API}/getUpdates",
            params={"offset": offset, "timeout": timeout},
            timeout=timeout + 5,
        )
        data = res.json()
        if data.get("ok"):
            return data.get("result", [])
    except Exception as e:
        print(f"[telegram] getUpdates failed: {e}")
    return []


def send_message(chat_id: int, text: str):
    """Send a text message to a Telegram chat."""
    # Telegram has a 4096-char limit per message — split if needed
    max_len = 4000
    for i in range(0, len(text), max_len):
        chunk = text[i: i + max_len]
        try:
            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )
        except Exception as e:
            print(f"[telegram] sendMessage failed: {e}")


def run_bot(handler):
    """
    Start a blocking polling loop.

    Args:
        handler: callable(chat_id: int, text: str)
                 called for every non-empty user message
    """
    print("[telegram] Bot started. Polling for messages...")
    offset = 0

    while True:
        updates = get_updates(offset=offset)

        for update in updates:
            offset = update["update_id"] + 1  # advance offset

            # Extract message text and chat id
            message = update.get("message", {})
            text = message.get("text", "").strip()
            chat_id = message.get("chat", {}).get("id")

            if not text or not chat_id:
                continue

            # Skip commands (e.g. /start)
            if text.startswith("/"):
                send_message(chat_id, "👋 Send me a stock news query, e.g.:\n`NVIDIA latest news 2026`")
                continue

            try:
                handler(chat_id, text)
            except Exception as e:
                print(f"[telegram] Handler error: {e}")
                send_message(chat_id, f"❌ Error processing your request: {e}")

        time.sleep(1)

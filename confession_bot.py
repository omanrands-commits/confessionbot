#!/usr/bin/env python3
"""
Anonymous Confession Bot for Telegram
======================================
- Members DM the bot → it posts anonymously to the group
- Auto-posts from confessions.txt every 15 seconds
- Set BOT_TOKEN and GROUP_ID before running

Usage:
    pip install python-telegram-bot
    python confession_bot.py
"""

import asyncio
import logging
import os
import random
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ─────────────────────────────────────────────
# CONFIGURATION — edit these before running
# ─────────────────────────────────────────────
BOT_TOKEN        = "7812345678:AAFxyz..."   # ← paste your token here
GROUP_ID         = -1003876111043            # ← already set
INTERVAL         = 15                        # seconds between auto-posts
CONFESSIONS_FILE = "confessions.txt"         # path to your confessions file
# ─────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Confession counter (persisted to a simple file) ──────────────────────────

COUNTER_FILE = "confession_counter.txt"

def load_counter() -> int:
    try:
        return int(Path(COUNTER_FILE).read_text().strip())
    except Exception:
        return 0

def save_counter(n: int) -> None:
    Path(COUNTER_FILE).write_text(str(n))

def next_number() -> int:
    n = load_counter() + 1
    save_counter(n)
    return n

# ── Pre-written confessions loader ───────────────────────────────────────────

def load_scheduled_confessions() -> list[str]:
    """
    Reads confessions.txt and returns a list of non-empty paragraphs.
    Each confession is separated by a blank line, OR you can use one per line.
    Automatically handles the Father_conf.txt format (numbered entries).
    """
    path = Path(CONFESSIONS_FILE)
    if not path.exists():
        logger.warning("confessions.txt not found — scheduled posts disabled.")
        return []

    text = path.read_text(encoding="utf-8")
    confessions = []

    # Try to detect the numbered format used in Father_conf.txt
    # Lines like:  #001\nWent 20x leverage...
    lines = text.splitlines()
    current: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Skip category headers like [ OVERLEVERAGED ]
        if stripped.startswith("[") and stripped.endswith("]"):
            continue

        # A line starting with # followed by digits marks a new entry
        if stripped.startswith("#") and stripped[1:4].isdigit():
            if current:
                confession_text = " ".join(current).strip()
                if confession_text:
                    confessions.append(confession_text)
            current = []
            continue

        if stripped:
            current.append(stripped)
        else:
            # Blank line — flush if we have content
            if current:
                confession_text = " ".join(current).strip()
                if confession_text:
                    confessions.append(confession_text)
                current = []

    # Flush last entry
    if current:
        confession_text = " ".join(current).strip()
        if confession_text:
            confessions.append(confession_text)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for c in confessions:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    logger.info("Loaded %d unique scheduled confessions.", len(unique))
    return unique


# ── Scheduled confession state ────────────────────────────────────────────────

class ScheduledState:
    def __init__(self):
        self.confessions: list[str] = []
        self.queue: list[str] = []

    def reload(self):
        self.confessions = load_scheduled_confessions()
        self.queue = list(self.confessions)
        random.shuffle(self.queue)
        logger.info("Queue refreshed with %d confessions.", len(self.queue))

    def next(self) -> str | None:
        if not self.queue:
            if not self.confessions:
                return None
            # Cycle: reload and shuffle again
            self.queue = list(self.confessions)
            random.shuffle(self.queue)
        return self.queue.pop(0) if self.queue else None


state = ScheduledState()


# ── Handlers ──────────────────────────────────────────────────────────────────

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message when someone /starts the bot."""
    if update.effective_chat.type != "private":
        return
    await update.message.reply_text(
        "🤫 *Anonymous Confession Bot*\n\n"
        "Send me your confession and I'll post it to the group — completely anonymously.\n\n"
        "Nobody will ever know it was you. Go ahead, unburden yourself.",
        parse_mode="Markdown",
    )


async def handle_dm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Receives a private message and posts it anonymously to the group."""
    if update.effective_chat.type != "private":
        return  # ignore messages inside groups

    text = update.message.text
    if not text or not text.strip():
        await update.message.reply_text("Please send a text message to confess.")
        return

    number = next_number()
    formatted = f"🤫 *Confession #{number}*\n\n{text.strip()}"

    try:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=formatted,
            parse_mode="Markdown",
        )
        await update.message.reply_text(
            f"✅ Your confession has been posted anonymously as *Confession #{number}*. "
            f"Your identity is safe with me.",
            parse_mode="Markdown",
        )
        logger.info("User %s submitted confession #%d", update.effective_user.id, number)
    except Exception as e:
        logger.error("Failed to post confession to group: %s", e)
        await update.message.reply_text(
            "⚠️ Something went wrong posting your confession. Please try again."
        )


# ── Scheduled posting job ─────────────────────────────────────────────────────

async def post_scheduled(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Called by JobQueue every INTERVAL seconds to post a pre-written confession."""
    confession = state.next()
    if not confession:
        logger.info("No scheduled confessions available.")
        return

    number = next_number()
    formatted = f"🤫 *Confession #{number}*\n\n{confession}"

    try:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=formatted,
            parse_mode="Markdown",
        )
        logger.info("Scheduled confession #%d posted.", number)
    except Exception as e:
        logger.error("Failed to post scheduled confession: %s", e)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print(
            "\n❌  ERROR: You haven't set your BOT_TOKEN.\n"
            "   1. Message @BotFather on Telegram\n"
            "   2. Create a bot with /newbot\n"
            "   3. Copy the token and replace YOUR_BOT_TOKEN_HERE in this file\n"
        )
        return

    # Load confessions file
    state.reload()

    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_dm))

    # Schedule the auto-posting job
    if state.confessions:
        app.job_queue.run_repeating(
            post_scheduled,
            interval=INTERVAL,
            first=INTERVAL,  # first post after one interval
        )
        logger.info(
            "Scheduled posting enabled: one confession every %d seconds.", INTERVAL
        )
    else:
        logger.warning("No confessions loaded — scheduled posting is OFF.")

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

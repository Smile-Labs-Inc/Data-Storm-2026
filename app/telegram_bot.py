"""Telegram bot for the Data-Storm-2026 Outlet Intelligence project.
"""

from __future__ import annotations

import io
import os
import sys
import time
import textwrap
import traceback
from contextlib import redirect_stdout
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from google import genai
from google.genai import types


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "Results"

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data() -> dict[str, pd.DataFrame]:
    """Load result CSVs into a name→DataFrame dictionary."""
    paths = {
        "outlet_intelligence": RESULTS_DIR / "outlet_intelligence.csv",
        "budget_allocations":  RESULTS_DIR / "smile_labs_budget_allocations_detailed.csv",
        "predictions":         RESULTS_DIR / "smile_labs_predictions.csv",
    }
    dfs: dict[str, pd.DataFrame] = {}
    for name, path in paths.items():
        if path.exists():
            dfs[name] = pd.read_csv(path)
            print(f"  Loaded {name}: {dfs[name].shape}")
        else:
            print(f"  Warning: {path} not found, skipping.")
    return dfs


# ---------------------------------------------------------------------------
# Gemini setup
# ---------------------------------------------------------------------------

def build_schema_summary(dfs: dict[str, pd.DataFrame]) -> str:
    """Return a compact text summary of available DataFrames for the prompt."""
    parts = []
    for name, df in dfs.items():
        cols = ", ".join(f"{c} ({df[c].dtype})" for c in df.columns)
        sample = df.head(2).to_string(index=False, max_colwidth=40)
        parts.append(
            f"DataFrame `{name}` — {len(df):,} rows, {len(df.columns)} columns\n"
            f"Columns: {cols}\n"
            f"Sample:\n{sample}"
        )
    return "\n\n".join(parts)


SYSTEM_PROMPT = textwrap.dedent("""
    You are a trade-marketing data analyst assistant for a beverage distributor in Sri Lanka.
    You answer questions about outlet sales predictions and budget allocation data.

    Available Python variables (already loaded as pandas DataFrames):
    {schema}

    RULES:
    - Answer ONLY using the available DataFrames listed above.
    - When you need to look something up, output ONLY a single Python code block
      (fenced with ```python ... ```) that computes the answer using the DataFrames.
    - The code must print its final result using print().
    - Do NOT include any explanation before the code block.
    - After you see the code output, write a clear, concise, plain-English answer
      in 2-4 sentences. No code in the final answer.
""").strip()


def extract_python_code(text: str) -> str | None:
    """Extract the first ```python ... ``` block from the model's response."""
    import re
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else None


def execute_code(code: str, namespace: dict) -> str:
    """Execute the code and capture stdout. Returns output or error."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            exec(code, namespace)  # noqa: S102
        return buf.getvalue().strip() or "(no output)"
    except Exception:
        return f"ERROR:\n{traceback.format_exc()}"


# Models to try in order if the primary is unavailable
MODEL_PRIORITY = ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds (doubles each retry)


def call_gemini_with_retry(client: genai.Client, contents: str) -> str:
    """Call Gemini with automatic retries and model fallback on 503 errors."""
    last_error = None
    for model in MODEL_PRIORITY:
        delay = RETRY_DELAY
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                )
                if attempt > 1 or model != MODEL_PRIORITY[0]:
                    print(f"  [Gemini] Success with model={model} on attempt {attempt}")
                return response.text.strip()
            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                is_503 = "503" in err_str or "UNAVAILABLE" in err_str
                is_429 = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
                if (is_503 or is_429) and attempt < MAX_RETRIES:
                    print(f"  [Gemini] {model} attempt {attempt} failed ({exc}). Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                elif is_503 or is_429:
                    print(f"  [Gemini] {model} exhausted retries, trying next model...")
                    break  # try next model
                else:
                    raise  # non-transient error, propagate immediately
    raise RuntimeError(f"All Gemini models unavailable. Last error: {last_error}")


def answer_question(question: str, dfs: dict[str, pd.DataFrame], client: genai.Client, schema: str) -> str:
    """Two-pass Gemini call: generate code → execute → produce final answer."""
    system = SYSTEM_PROMPT.format(schema=schema)

    # Pass 1: Ask Gemini to write Python code
    reply1 = call_gemini_with_retry(
        client,
        f"{system}\n\nUser question: {question}",
    )

    code = extract_python_code(reply1)

    if code:
        # Execute the generated code with the DataFrames in scope
        namespace = {name: df.copy() for name, df in dfs.items()}
        namespace["pd"] = pd
        code_output = execute_code(code, namespace)

        # Pass 2: Ask Gemini to turn the code output into a plain-English answer
        reply2 = call_gemini_with_retry(
            client,
            (
                f"{system}\n\nUser question: {question}\n\n"
                f"You ran this Python code and got the following output:\n{code_output}\n\n"
                "Now write a clear, concise plain-English answer based on this output. "
                "No code, no markdown formatting, no asterisks."
            ),
        )
        return reply2
    else:
        # Model answered directly (simple factual question)
        return reply1


# ---------------------------------------------------------------------------
# Bot handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.first_name}! 👋 I'm your Outlet Intelligence Assistant.\n\n"
        "I have access to the Data Storm 2026 outlet predictions and budget allocation data. "
        "Ask me anything about the outlets, provinces, distributors, or the spend plan!\n\n"
        "Example questions:\n"
        "• Which outlet has the highest predicted potential?\n"
        "• How many outlets in the Western province received budget?\n"
        "• What is the total allocated budget?\n"
        "• Which distributor has the most outlets?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dfs: dict[str, pd.DataFrame] = context.bot_data["dfs"]
    client: genai.Client = context.bot_data["model"]
    schema: str = context.bot_data["schema"]

    question = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        print(f"[Query] {question}")
        answer = answer_question(question, dfs, client, schema)
        await update.message.reply_text(answer)
    except Exception as exc:
        print(f"[Error] {exc}")
        await update.message.reply_text(
            f"Sorry, something went wrong while answering your question. "
            f"Please try rephrasing it.\n\nError: {str(exc)[:200]}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is not set in your .env file.")
        sys.exit(1)
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is not set in your .env file.")
        sys.exit(1)

    print("Loading data...")
    dfs = load_data()
    if not dfs:
        print("No data files found. Please run the pipeline first.")
        sys.exit(1)

    print("Initializing Gemini client (gemini-2.5-flash)...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    model = client

    schema = build_schema_summary(dfs)

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.bot_data["dfs"] = dfs
    application.bot_data["model"] = client
    application.bot_data["schema"] = schema

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Telegram bot is running. Press Ctrl-C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

"""
config.py - Central settings for the chatbot (Google Gemini version).

Everything you might want to tweak (model, token limit, history size, exit
words) lives here, so you never have to hunt through app.py.

Secrets such as the API key are read from a `.env` file, NEVER hard-coded.
"""

import os

from dotenv import load_dotenv

# Read the .env file in the project folder and load its values into the
# process environment. If there is no .env file, this quietly does nothing.
load_dotenv()


def _get_int(name: str, default: int) -> int:
    """Read an integer setting from the environment, falling back to a default."""
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        return int(raw_value)
    except ValueError:
        print(f"Warning: {name}={raw_value!r} is not a number. Using {default} instead.")
        return default


# --- Secrets (come from .env) -------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# --- Model settings (can be overridden in .env) --------------------------------
# A small, fast "Flash-Lite" model: ideal for learning and available on the
# free tier at the time of writing. Model names change over time - if you get
# a "model not found" message, pick a current name from Google AI Studio and
# set GEMINI_MODEL in your .env file.
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Maximum length of each reply (in tokens; 1 token is roughly 3/4 of a word).
# Gemini models may spend part of this budget on internal "thinking", so we
# keep it generous. Raise it if replies ever come back cut off or empty.
MAX_TOKENS = _get_int("MAX_TOKENS", 2048)

# --- Conversation memory --------------------------------------------------------
# Only the most recent N messages (user + assistant combined) are sent to the
# API. This keeps requests small, fast and cheap during long chats.
MAX_HISTORY_MESSAGES = _get_int("MAX_HISTORY_MESSAGES", 20)

# --- Network behaviour ----------------------------------------------------------
REQUEST_TIMEOUT_SECONDS = 30.0  # give up if the API doesn't answer in time

# --- Chat interface ---------------------------------------------------------------
ASSISTANT_NAME = "AI Assistant"
EXIT_COMMANDS = {"exit", "quit", "bye"}

# The value shipped in .env.example - used to detect "you forgot to paste a key".
PLACEHOLDER_API_KEY = "your_api_key_here"

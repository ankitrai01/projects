"""
app.py - A terminal AI chatbot powered by the Google Gemini API.

Run it with:   python app.py

How it works (the 30-second version):
  1. Read the user's message and validate it.
  2. Add it to `history` (a list of {"role": ..., "content": ...} dictionaries).
  3. Send the system prompt + recent history to Gemini.
  4. Print Gemini's reply and add it to `history` too.
  5. Repeat. Because the history is re-sent every turn, the model "remembers"
     what was said earlier and can answer follow-up questions.
"""

import sys

import httpx  # installed automatically together with google-genai
from google import genai
from google.genai import errors, types

import config
from prompts import GREETING, SYSTEM_PROMPT

# A single chat message looks like: {"role": "user" or "assistant", "content": "text"}
# (This is our own simple format. We convert it for Gemini just before sending.)
Message = dict[str, str]


# ------------------------------------------------------------------------------
# Small helpers for printing
# ------------------------------------------------------------------------------
def clear_line() -> None:
    """Erase the temporary "(thinking...)" text from the current terminal line."""
    print(" " * 20, end="\r", flush=True)


def print_error(message: str) -> None:
    """Show a friendly, clearly-marked error message (without crashing)."""
    clear_line()
    print(f"\n[!] {message}\n")


def print_assistant(message: str) -> None:
    """Print a line spoken by the assistant."""
    print(f"\n{config.ASSISTANT_NAME}: {message}\n")


# ------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------
def create_client() -> genai.Client:
    """Create the API client, or exit with clear instructions if no key is set."""
    api_key = config.GEMINI_API_KEY

    if not api_key or api_key == config.PLACEHOLDER_API_KEY:
        print_error(
            "No API key found.\n"
            "    1. Copy .env.example to a new file named .env\n"
            "    2. Open .env and replace the placeholder with your real key\n"
            "       (get one at https://aistudio.google.com/apikey)\n"
            "    3. Run this program again"
        )
        sys.exit(1)

    return genai.Client(
        api_key=api_key,
        # Gemini's timeout is in MILLISECONDS, so we convert from seconds.
        http_options=types.HttpOptions(timeout=int(config.REQUEST_TIMEOUT_SECONDS * 1000)),
    )


# ------------------------------------------------------------------------------
# Conversation memory
# ------------------------------------------------------------------------------
def trim_history(history: list[Message]) -> list[Message]:
    """
    Return only the most recent messages to send to the API.

    We keep the full transcript in memory but send just the last N messages
    (see MAX_HISTORY_MESSAGES in config.py) to control cost and speed.
    """
    recent = history[-config.MAX_HISTORY_MESSAGES :]

    # The conversation should start with a user message, so drop any leading
    # assistant message left over after trimming.
    while recent and recent[0]["role"] != "user":
        recent = recent[1:]

    return recent


def to_gemini_contents(messages: list[Message]) -> list[types.Content]:
    """
    Convert our simple messages into Gemini's format.

    The only real difference: Gemini calls the assistant's role "model"
    instead of "assistant", and wraps the text inside "parts".
    """
    contents = []
    for message in messages:
        role = "model" if message["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=message["content"])]))
    return contents


# ------------------------------------------------------------------------------
# Talking to the API
# ------------------------------------------------------------------------------
def report_client_error(error: errors.ClientError) -> None:
    """Explain 4xx errors (problems with the request, key or quota) in plain words."""
    code = error.code
    text = str(error.message or "").lower()

    if code == 429:
        print_error(
            "Rate limit or free-tier quota reached. Wait a minute and try again.\n"
            "    If it keeps happening, you may have used up today's free quota."
        )
    elif code in (401, 403) or (code == 400 and "api key" in text):
        print_error(
            "Authentication failed: your API key looks invalid, disabled or revoked.\n"
            "    Check GEMINI_API_KEY in your .env file (create a new key if needed), then restart."
        )
    elif code == 404:
        print_error(
            f"The model '{config.MODEL_NAME}' was not found.\n"
            "    Set GEMINI_MODEL in your .env file to a current model name from Google AI Studio."
        )
    else:
        print_error(f"The API rejected the request (status {code}): {error.message}")


def ask_gemini(client: genai.Client, history: list[Message]):
    """
    Send the conversation to Gemini and return the API response.

    If anything goes wrong, print a helpful message and return None instead of
    crashing, so the user can keep chatting (or fix the problem and retry).
    """
    try:
        return client.models.generate_content(
            model=config.MODEL_NAME,
            contents=to_gemini_contents(trim_history(history)),  # the conversation so far
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,  # the assistant's role / personality
                max_output_tokens=config.MAX_TOKENS,
                # We don't use tools/function calling, so switch it off. (This also
                # stops the SDK from printing a confusing "AFC" warning.)
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )

    # Order matters: the more specific errors must come BEFORE the general ones.
    except errors.ClientError as error:  # 4xx: bad key, bad model, rate limit...
        report_client_error(error)
    except errors.ServerError as error:  # 5xx: Google's side had a problem
        print_error(f"Gemini is having trouble right now (status {error.code}). Please try again shortly.")
    except errors.APIError as error:  # any other API error
        print_error(f"The API returned an error (status {error.code}): {error.message}")
    except httpx.TimeoutException:
        print_error("The request timed out. Please check your connection and try again.")
    except httpx.TransportError:  # no internet, DNS failure, connection dropped...
        print_error("Couldn't reach the Gemini API. Please check your internet connection.")
    except Exception as error:  # last-resort safety net for anything unexpected
        print_error(f"Something unexpected went wrong: {error}")

    return None


def extract_text(response) -> str:
    """Pull the plain reply text out of an API response (empty string if none)."""
    return (response.text or "").strip()


def finish_reason_of(response):
    """Return the 'why did the model stop' value of the first candidate, if any."""
    candidates = response.candidates or []
    return candidates[0].finish_reason if candidates else None


def explain_empty_response(response) -> str:
    """Turn an empty response into a helpful explanation."""
    feedback = response.prompt_feedback
    if feedback and feedback.block_reason:
        return (
            f"Gemini's safety filter blocked this message ({feedback.block_reason.name}). "
            "Try rephrasing your question."
        )

    reason = finish_reason_of(response)
    if reason == types.FinishReason.MAX_TOKENS:
        return (
            "The reply ran out of space before any text was produced. "
            "Increase MAX_TOKENS in your .env file (for example 4096) and try again."
        )
    if reason is not None and reason != types.FinishReason.STOP:
        return f"Gemini stopped without giving a reply (reason: {reason.name}). Try rephrasing."

    return "The API returned an unexpected (empty) response. Please try again."


# ------------------------------------------------------------------------------
# Main chat loop
# ------------------------------------------------------------------------------
def main() -> None:
    client = create_client()
    history: list[Message] = []  # starts empty; grows with every turn

    print("=" * 60)
    print("  AI Chatbot Assistant (Gemini)")
    print("  Type 'exit', 'quit' or 'bye' to leave | '/clear' resets memory")
    print("=" * 60)
    print_assistant(GREETING)

    while True:
        # --- 1. Read input --------------------------------------------------------
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):  # Ctrl+C or Ctrl+D
            print_assistant("Goodbye!")
            break

        # --- 2. Validate input ----------------------------------------------------
        if not user_input:
            print_assistant("I didn't catch that - please type a question.")
            continue  # never send an empty request to the API

        command = user_input.lower().strip("!. ")  # so "Bye!" also works

        if command in config.EXIT_COMMANDS:
            print_assistant("Goodbye!")
            break

        if command == "/clear":
            history.clear()
            print_assistant("Memory cleared. Let's start a fresh conversation!")
            continue

        # --- 3. Remember what the user said, then ask Gemini ----------------------
        history.append({"role": "user", "content": user_input})

        print("(thinking...)", end="\r", flush=True)
        response = ask_gemini(client, history)
        clear_line()  # erase the "thinking" text

        # If the request failed (error already shown), forget the failed question.
        # Otherwise the next message would create two "user" messages in a row.
        if response is None:
            history.pop()
            continue

        reply = extract_text(response)
        if not reply:
            print_error(explain_empty_response(response))
            history.pop()
            continue

        # --- 4. Show and remember the answer --------------------------------------
        history.append({"role": "assistant", "content": reply})
        print_assistant(reply)

        if finish_reason_of(response) == types.FinishReason.MAX_TOKENS:
            print("    (Note: this reply was cut short. Ask me to 'continue' for the rest.)\n")


if __name__ == "__main__":
    main()

# AI Chatbot Assistant (Google Gemini)

A beginner-friendly, terminal-based AI chatbot built with **Python** and the **Google Gemini API**. It answers questions in a predefined role (a patient assistant who explains technical ideas in simple language) and remembers the conversation, so follow-up questions like *"What are its advantages?"* just work.

## Features

- **LLM API integration** using the official Google Gen AI Python SDK (`google-genai`)
- **Secure API key handling** with a `.env` file (the key is never hard-coded or committed)
- **Role-based assistant** driven by an easy-to-edit system prompt in `prompts.py`
- **Conversation history** sent with every request so follow-up questions are understood
- **Prompt engineering**: a structured prompt covering role, audience, style, honesty and memory cues
- **Input validation**: empty input is caught locally, never sent to the API
- **Clean exit commands**: `exit`, `quit`, `bye` (plus Ctrl+C), and `/clear` to reset memory
- **Robust error handling** for invalid keys, rate limits, network failures, blocked or empty responses; the app never crashes mid-chat

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.10+ | Core language |
| `google-genai` (Google Gen AI SDK) | Calling the Gemini API |
| python-dotenv | Loading secrets from `.env` |

No web framework and no database are needed.

## Project Structure

```text
ai-chatbot-assistant-gemini/
│
├── app.py              # Chat loop, history, API call, error handling
├── config.py           # Settings (model, token limit, history size, exit words)
├── prompts.py          # System prompt (the assistant's role) and greeting
├── requirements.txt    # Python dependencies
├── .env.example        # Template for your secrets (safe to commit)
├── .env                # YOUR real API key (you create this; never committed)
├── .gitignore          # Keeps .env, venv and caches out of Git
└── README.md
```

## Installation

**1. Open a terminal inside the project folder**

```bash
cd ai-chatbot-assistant-gemini
```

**2. Create a virtual environment**

```bash
# Windows
python -m venv venv

# macOS / Linux
python3 -m venv venv
```

**3. Activate it**

```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

**4. Install the dependencies**

```bash
pip install -r requirements.txt
```

## Environment Variable Setup

1. Open Google AI Studio (<https://aistudio.google.com/apikey>) and sign in with a Google account.
2. Click **Create API key** and choose a project (import one first if asked).
3. Copy the key.
4. Copy the template to a real `.env` file:

   ```bash
   # Windows
   copy .env.example .env

   # macOS / Linux
   cp .env.example .env
   ```

5. Open `.env` and replace the placeholder:

   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

   Paste the key right after the `=`, with no quotes and no spaces.

> **Security:** `.env` is listed in `.gitignore`, so it won't be uploaded to GitHub. Never paste your key into source code, screenshots or chat messages. If a key is ever exposed, delete it in AI Studio and create a new one.

> **Free tier note:** Google offers a rate-limited free tier for the Gemini API. Limits can change, so check your AI Studio dashboard. On the free tier, Google may use your prompts to improve its products, so don't send private or personal information.

Optional settings (see `.env.example`): `GEMINI_MODEL`, `MAX_TOKENS`, `MAX_HISTORY_MESSAGES`. Model names change over time; if you see a "model not found" message, pick a current model name in AI Studio and set `GEMINI_MODEL`.

## How to Run

```bash
python app.py
```

(Use `python3 app.py` on macOS/Linux if `python` isn't found.)

## Example Conversation

```text
============================================================
  AI Chatbot Assistant (Gemini)
  Type 'exit', 'quit' or 'bye' to leave | '/clear' resets memory
============================================================

AI Assistant: Hello! How can I help you?

You: What is machine learning?

AI Assistant: Machine learning is a way of teaching computers to find patterns in
examples instead of giving them step-by-step rules. Think of how a child learns
to recognise dogs by seeing many dogs rather than memorising a definition...

You: Explain it with an example.

AI Assistant: Sure! Imagine an email app learning to spot spam. You show it
thousands of emails already labelled "spam" or "not spam"...

You: exit

AI Assistant: Goodbye!
```

## How the Prompt Improves Response Quality

The system prompt in `prompts.py` is deliberately structured:

| Prompt element | Effect on answers |
|---|---|
| **Role** ("friendly, patient assistant...") | Consistent tone and focus |
| **Audience** ("assume a beginner") | Right difficulty level; jargon gets defined |
| **Format rules** (direct answer first, then an analogy, under ~200 words) | Predictable, scannable responses |
| **Honesty rule** ("say so if unsure") | Fewer confident-sounding guesses |
| **Memory cue** ("it / its / that refer to the latest topic") | Better follow-up understanding |

Change the role in `prompts.py` (for example, to a math tutor) and the same code becomes a different assistant.

## How Conversation Memory Works

The API is stateless: it only knows what you send in each request. The app keeps a Python list, `history`, of `{"role": ..., "content": ...}` messages and sends the most recent ones every turn. Just before sending, `to_gemini_contents()` converts them to Gemini's format (where the assistant's role is called `"model"`).

## Error Handling

The app catches errors around every API call, prints a friendly message and lets you keep chatting.

| Situation | What happens |
|---|---|
| Empty input | Friendly reminder; nothing is sent to the API |
| Missing / placeholder API key | Clear setup instructions, then a clean exit at startup |
| Invalid, disabled or revoked key (400/401/403) | Tells you to check `.env` |
| Rate limit / free quota (429) | Asks you to wait and retry |
| Timeout / no internet | Connection-specific message |
| Server errors (5xx) | Shows the status code and suggests retrying |
| Unknown model name (404) | Points you to `GEMINI_MODEL` in `.env` |
| Safety-blocked, empty or cut-off response | Explains why and suggests what to change |
| Anything else | Caught by a final safety net |

When a request fails, the user's message is removed from history so the conversation never contains two consecutive user messages.

## Future Improvements

- Stream replies token-by-token for a more responsive feel
- Save and load conversations from a JSON file
- Summarise old messages instead of dropping them
- Let users switch personas with a command (e.g. `/role tutor`)
- Track token usage per session
- Add unit tests with a mocked API client
- Build a web UI (Streamlit or Flask) on top of the same core logic

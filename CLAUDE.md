# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Private Telegram bot that:
- Accepts messages only from authorized users (whitelist by Telegram user ID)
- Processes messages via an LLM (OpenRouter API)
- Persists conversations to Google Sheets

The full specification is in `agente-telegram-ia.md` (Portuguese).

## Tech Stack

| Layer | Technology |
|---|---|
| Bot | `pyTelegramBotAPI` |
| AI | OpenRouter API (`LLM_API_KEY`) |
| Database | Google Sheets via `gspread` |
| Hosting | Railway or Oracle Cloud Free Tier |

## Environment Variables (.env)

```
TELEGRAM_TOKEN_BOTFATHER=        # Token do @BotFather
AUTHORIZED_USER_IDS=111,222      # IDs separados por vírgula (obter via @userinfobot)
LLM_API_KEY=                     # OpenRouter API key
GOOGLE_SHEET_NAME=MensagensBot   # Nome exato da planilha (não URL)
```

## Project Structure

```
main.py               # Bot entry point, polling loop
config.py             # Load .env vars, parse AUTHORIZED_USER_IDS
handlers/
  message_handler.py  # @bot.message_handler — orchestrates auth → AI → db → reply
  auth.py             # is_authorized(user_id)
ai/
  llm_client.py       # OpenRouter API call → str
db/
  sheets.py           # save_to_db() via gspread
google/               # Google Service Account credentials (never commit — in .gitignore)
  don-meu-agente-fa91a75f124b.json
requirements.txt
.env
```

## Core Message Flow

1. User sends message → `handle_message()` in `handlers/message_handler.py`
2. `auth.py` checks `user_id` against `AUTHORIZED_USER_IDS` — unauthorized → `"❌ Acesso não autorizado."`
3. `ai/llm_client.py` calls OpenRouter API
4. `db/sheets.py` saves `{timestamp, user_id, username, message, ai_response}` to Google Sheets
5. Bot replies with AI response

## Google Sheets Setup (already configured)

- Service Account: `don-927@don-meu-agente.iam.gserviceaccount.com`
- Credentials file: `google/don-meu-agente-fa91a75f124b.json`
- The target spreadsheet must be shared with the Service Account email above
- Open sheet in code: `client.open(GOOGLE_SHEET_NAME).sheet1`

## Dependencies

```
pyTelegramBotAPI
openai          # OpenRouter is OpenAI-compatible
gspread
oauth2client
python-dotenv
```

Install: `pip install -r requirements.txt`

Run: `python main.py`

## Authorization Design

`AUTHORIZED_USER_IDS` is parsed at startup as a list of ints. For dynamic authorization without restarts, store IDs in the database instead.

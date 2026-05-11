# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Personal finance Telegram bot. The user sends expenses in natural language (e.g., "Almoço 35 reais", "Gasolina 120", "Netflix 45,90 streaming"), the LLM extracts structured data, and saves it to Google Sheets so the user can later visualize expenses in a frontend dashboard.

## Tech Stack

| Layer | Technology |
|---|---|
| Bot | `pyTelegramBotAPI` |
| AI | OpenRouter API (`LLM_API_KEY`) — model `openai/gpt-4o-mini` |
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
  llm_client.py       # OpenRouter API call → str (needs system prompt for expense extraction)
db/
  sheets.py           # save_to_db() via gspread
google/               # Google Service Account credentials (never commit — in .gitignore)
  don-meu-agente-6886231ffdfe.json
requirements.txt
.env
```

## Core Message Flow

1. User sends expense message → `handle_message()` in `handlers/message_handler.py`
2. `auth.py` checks `user_id` against `AUTHORIZED_USER_IDS` — unauthorized → `"❌ Acesso não autorizado."`
3. `ai/llm_client.py` calls OpenRouter with a **system prompt** to extract structured expense JSON from natural language
4. `db/sheets.py` saves the structured expense row to Google Sheets
5. Bot replies confirming what was recorded

## Google Sheets Schema (target columns)

| A: timestamp | B: user_id | C: username | D: mensagem_original | E: valor | F: categoria | G: descricao | H: data_gasto |

The LLM should return JSON like:
```json
{"valor": 35.00, "categoria": "Alimentação", "descricao": "Almoço", "data_gasto": "2026-05-08"}
```

## Google Sheets Setup

- Service Account: `don-927@don-meu-agente.iam.gserviceaccount.com`
- Credentials file: `google/don-meu-agente-6886231ffdfe.json`
- The target spreadsheet must be shared with the Service Account email above
- Open sheet in code: `client.open(GOOGLE_SHEET_NAME).sheet1`

## Current Implementation State

The code structure is in place and functional as a **generic chatbot**. It still needs:
1. A system prompt in `llm_client.py` so the LLM extracts expense data (valor, categoria, descricao, data_gasto) as JSON
2. Updated `db/sheets.py` columns to match the expense schema above
3. Updated `message_handler.py` to parse LLM JSON and build the structured row

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

## Suggested Expense Categories

Alimentação, Transporte, Moradia, Saúde, Lazer, Educação, Streaming, Roupas, Outros

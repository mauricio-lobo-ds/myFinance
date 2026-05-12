# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Personal finance Telegram bot. The user sends expenses or queries in natural language, the LLM classifies the intent, and the bot either saves the expense to Google Sheets or returns a summary.

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
  message_handler.py  # Handlers: text, photo, /gastos, /comprovante, /help
  auth.py             # is_authorized(user_id)
ai/
  llm_client.py       # OpenRouter API call — returns intent-classified JSON
db/
  sheets.py           # save_to_db(), get_gastos(), get_comprovantes() via gspread
google/               # Google Service Account credentials (never commit — in .gitignore)
  don-meu-agente-6886231ffdfe.json
tests/
  conftest.py         # Mocks for gspread, openai, telebot, oauth2client
  test_auth.py
  test_sheets.py
  test_llm_client.py
requirements.txt
.env
```

## Core Message Flow

All text messages go through `ask_llm()` which returns a JSON with an `intent` field. `handle_message()` routes based on intent:

| Intent | Trigger examples | Action |
|---|---|---|
| `registrar` | "Almoço 35 reais", "Netflix 45,90" | Saves expense to Sheets |
| `gastos` | "Quanto gastei esse mês?", "Resumo de abril" | Returns spending summary |
| `comprovantes` | "Mostra meus comprovantes de maio" | Sends receipt photos |
| `ajuda` | "O que você faz?", "ajuda" | Shows /help |
| `invalido` | Greetings, random text | Fallback message |

Photos with captions are handled separately by `handle_photo()` — caption is the expense description, photo is saved as `telegram_file_id` in column I.

## LLM Response Format

```json
{"intent": "registrar", "valido": true, "valor": 35.00, "categoria": "Alimentação", "descricao": "Almoço", "data_gasto": "2026-05-08"}
{"intent": "registrar", "valido": false}
{"intent": "gastos", "periodo": "2026-05"}
{"intent": "comprovantes", "mes": "2026-05"}
{"intent": "ajuda"}
{"intent": "invalido"}
```

## Google Sheets Schema

| A: timestamp | B: user_id | C: username | D: mensagem_original | E: valor | F: categoria | G: descricao | H: data_gasto | I: telegram_file_id |

Headers are auto-created at startup by `_ensure_headers()` in `sheets.py`.

## Google Sheets Setup

- Service Account: `don-927@don-meu-agente.iam.gserviceaccount.com`
- Credentials file: `google/don-meu-agente-6886231ffdfe.json`
- The target spreadsheet must be shared with the Service Account email above
- Note: Service Accounts have no Drive storage quota — file uploads go via Telegram file_id only

## Slash Commands (also work as natural language)

- `/help` or `/ajuda` — list commands
- `/gastos [YYYY-MM|YYYY]` — expense summary for period (default: current month)
- `/comprovante [YYYY-MM]` — last 5 receipts for period (default: current month)

## Receipt Storage

Receipts are stored as Telegram `file_id` (column I). To retrieve: `/comprovante` command resends the photo via bot. Google Drive was discarded — service accounts have no storage quota on personal Gmail.

## Running Tests

```
python -m pytest tests/ -v
```

17 tests covering auth, sheets logic, and LLM client. No external calls — all dependencies mocked in `tests/conftest.py`.

## Dependencies

```
pyTelegramBotAPI
openai          # OpenRouter is OpenAI-compatible
gspread
oauth2client
python-dotenv
google-api-python-client
pytest
```

Install: `python -m pip install -r requirements.txt`

Run: `python main.py`

## Authorization Design

`AUTHORIZED_USER_IDS` is parsed at startup as a list of ints. For dynamic authorization without restarts, store IDs in the database instead.

## Expense Categories

Alimentação, Transporte, Moradia, Saúde, Lazer, Educação, Streaming, Roupas, Outros

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
USER_NAMES=111:Mauricio,222:Ana  # Nomes amigáveis por ID (opcional)
LLM_API_KEY=                     # OpenRouter API key
GOOGLE_SHEET_NAME=MensagensBot   # Nome exato da planilha (não URL)
GOOGLE_CREDENTIALS_JSON=         # Conteúdo do JSON da Service Account (para deploy)
```

## Project Structure

```
main.py               # Bot entry point, polling loop
config.py             # Load .env vars, parse AUTHORIZED_USER_IDS, USER_NAMES
handlers/
  message_handler.py  # All handlers: text, photo, commands, inline + reply keyboards
  auth.py             # is_authorized(user_id)
ai/
  llm_client.py       # OpenRouter API call — returns intent-classified JSON
db/
  sheets.py           # save_to_db(), get_gastos(), get_gastos_todos(),
                      # get_comprovantes(), get_comprovantes_todos() via gspread
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

Quick-action buttons ("💰 Gastos", "📎 Comprovantes", "❓ Ajuda") are intercepted in `handle_message()` before the LLM call — no tokens consumed. All other text goes through `ask_llm()`:

| Intent | Trigger examples | Action |
|---|---|---|
| `registrar` | "Almoço 35 reais", "Netflix 45,90" | Saves expense to Sheets |
| `gastos` | "Quanto gastei esse mês?", "Resumo de abril" | Interactive keyboard flow |
| `comprovantes` | "Mostra meus comprovantes de maio" | Interactive keyboard flow |
| `ajuda` | "O que você faz?", "ajuda" | Shows /help |
| `invalido` | Greetings, random text | Fallback message |

Photos with captions are handled separately by `handle_photo()` — caption is the expense description, photo is saved as `telegram_file_id` in column I.

## Interactive Keyboard Flow (gastos and comprovantes)

Both `/gastos` and `/comprovante` use a 2-step inline keyboard flow:

1. **Who**: [👤 Meus] [👥 Todos] [🔍 Por pessoa]
2. **Period**: [📅 Mês atual] [⬅️ Mês passado] [📆 Este ano]

If the LLM already extracted a period (natural language) or the user passed one as argument (`/gastos 2026-05`), step 2 is skipped.

State is stored in `_gastos_state` / `_comp_state` dicts keyed by `(chat_id, message_id)`. Callback prefixes: `gastos:`, `comp:`, `lanca:`.

After the gastos summary, a "📋 Ver lançamentos" inline button shows individual entries (max 30 most recent).

## Reply Keyboard (persistent bottom buttons)

Shown on `/start` and `/help`. Three buttons:
- **💰 Gastos** → starts gastos interactive flow
- **📎 Comprovantes** → starts comprovantes interactive flow
- **❓ Ajuda** → shows help message

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

## Slash Commands

- `/start` — welcome message + shows reply keyboard
- `/help` or `/ajuda` — list commands + shows reply keyboard
- `/gastos [YYYY-MM|YYYY]` — interactive expense summary
- `/comprovante [YYYY-MM]` — interactive receipt viewer

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

`AUTHORIZED_USER_IDS` is parsed at startup as a list of ints. `USER_NAMES` maps IDs to friendly display names used in summaries and keyboard labels. For dynamic authorization without restarts, store IDs in the database instead.

## Expense Categories

Alimentação, Transporte, Moradia, Saúde, Lazer, Educação, Streaming, Roupas, Outros

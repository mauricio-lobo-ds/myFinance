---
name: myfinance project context
description: Purpose and current state of the myfinance Telegram bot project
type: project
---

Personal finance Telegram bot (myfinance). User sends expenses in natural language, LLM extracts structured data (valor, categoria, descricao, data_gasto), saved to Google Sheets for later frontend visualization.

**Why:** User wants a frictionless way to log expenses via Telegram and view them in a dashboard.

**How to apply:** When suggesting changes, always keep structured expense extraction as the core concern — the LLM must return parseable JSON, and the Sheets schema must match the expense columns (timestamp, user_id, username, mensagem_original, valor, categoria, descricao, data_gasto).

Current state (2026-05-08): Code structure is complete as a generic chatbot. Three changes still needed:
1. System prompt in `ai/llm_client.py` for expense JSON extraction
2. Updated columns in `db/sheets.py` 
3. Updated `handlers/message_handler.py` to parse JSON and build structured row

Google Sheets service account: `don-927@don-meu-agente.iam.gserviceaccount.com`
Credentials file: `google/don-meu-agente-6886231ffdfe.json`

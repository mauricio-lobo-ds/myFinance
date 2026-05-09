# 🤖 Agente de IA Privado no Telegram com Persistência em Banco de Dados

## Visão Geral

Construir um bot do Telegram que:
- Recebe mensagens apenas de usuários **autorizados**
- Processa as mensagens com uma **IA** (Claude ou OpenAI)
- Salva as mensagens (e opcionalmente as respostas) num **banco de dados**

---

## Arquitetura

```
Usuário Telegram
      ↓
  Bot Telegram (TOKEN via @BotFather)
      ↓
  Backend Python
   ├── Verificação de autorização (whitelist de IDs)
   ├── Processamento com IA (opcional)
   └── Persistência
         ├── Google Sheets (mais simples)
         ├── SQLite (local)
         └── Supabase / PostgreSQL (nuvem)
```

---

## Stack Sugerida

| Camada | Tecnologia | Motivo |
|---|---|---|
| Bot | `pyTelegramBotAPI` | Simples e bem documentado |
| IA | Claude API (Anthropic) | Melhor custo-benefício |
| Banco | Google Sheets ou Supabase | Fácil de visualizar os dados |
| Hospedagem | Railway ou VPS Oracle Free | Grátis e sempre ligado |

---

## Controle de Acesso

```python
AUTHORIZED_USERS = [123456789, 987654321]  # IDs do Telegram

def is_authorized(user_id: int) -> bool:
    return user_id in AUTHORIZED_USERS
```

> Dica: obter seu ID pelo @userinfobot no Telegram.

Alternativa mais robusta: salvar os IDs autorizados no próprio banco de dados e carregar dinamicamente, sem precisar reiniciar o bot para adicionar novos usuários.

---

## Estrutura do Projeto

```
telegram-agent/
├── main.py               # Entry point do bot
├── config.py             # Tokens, IDs autorizados, configs
├── handlers/
│   ├── message_handler.py  # Lógica de recebimento
│   └── auth.py             # Verificação de acesso
├── ai/
│   └── claude_client.py    # Integração com a IA
├── db/
│   ├── sheets.py           # Integração Google Sheets
│   └── supabase_client.py  # Alternativa com Supabase
├── credentials.json        # Credenciais Google (não commitar!)
├── requirements.txt
└── .env                    # Variáveis de ambiente (não commitar!)
```

---

## Exemplo de Fluxo Principal

```python
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.from_user.id

    # 1. Verifica autorização
    if not is_authorized(user_id):
        bot.reply_to(message, "❌ Acesso não autorizado.")
        return

    # 2. Processa com IA (opcional)
    ai_response = ask_claude(message.text)

    # 3. Salva no banco
    save_to_db({
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "username": message.from_user.username,
        "message": message.text,
        "ai_response": ai_response,
    })

    # 4. Responde ao usuário
    bot.reply_to(message, ai_response)
```

---

## Integração com Google Sheets

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("NomeDaPlanilha").sheet1

def save_to_db(data: dict):
    sheet.append_row([
        data["timestamp"],
        data["user_id"],
        data["username"],
        data["message"],
        data["ai_response"],
    ])
```

**Passos para configurar:**
1. Google Cloud Console → Criar projeto
2. Ativar APIs: Google Sheets API + Google Drive API
3. Criar Service Account → Baixar `credentials.json`
4. Compartilhar a planilha com o e-mail da Service Account

---

## Integração com Claude (Anthropic)

```python
import anthropic

client = anthropic.Anthropic(api_key="SUA_CHAVE_AQUI")

def ask_claude(user_message: str) -> str:
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": user_message}]
    )
    return response.content[0].text
```

---

## Variáveis de Ambiente (.env)

```env
TELEGRAM_TOKEN=seu_token_aqui
ANTHROPIC_API_KEY=sua_chave_aqui
AUTHORIZED_USER_IDS=123456789,987654321
GOOGLE_SHEET_NAME=NomeDaPlanilha
```

---

## Dependências (requirements.txt)

```
pyTelegramBotAPI
anthropic
gspread
oauth2client
python-dotenv
```

---

## Hospedagem

### Railway (recomendado para começar)
1. Criar conta em railway.app
2. Conectar repositório GitHub
3. Adicionar variáveis de ambiente no painel
4. Deploy automático a cada push

### Oracle Cloud Free Tier (recomendado para produção)
- VM Ubuntu gratuita para sempre
- SSH + `systemd` para manter o bot rodando
- Sem limite de horas

---

## Funcionalidades Futuras (ideias)

- [ ] Gerenciar lista de usuários autorizados via comando `/authorize`
- [ ] Suporte a áudios (transcrição via Whisper)
- [ ] Suporte a imagens (visão computacional)
- [ ] Histórico de conversa por usuário (memória do agente)
- [ ] Dashboard web para visualizar as mensagens salvas
- [ ] Comandos customizados (`/resumir`, `/traduzir`, etc.)
- [ ] Notificações proativas (bot manda mensagem sem ser perguntado)
- [ ] Rate limiting por usuário

---

## Referências

- [pyTelegramBotAPI Docs](https://github.com/eternnoir/pyTelegramBotAPI)
- [Anthropic API Docs](https://docs.anthropic.com)
- [gspread Docs](https://docs.gspread.org)
- [Supabase Python Client](https://supabase.com/docs/reference/python)
- [Railway Deploy Docs](https://docs.railway.app)

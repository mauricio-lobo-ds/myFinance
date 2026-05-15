# 💰 MyFinance Bot

Bot pessoal de finanças no Telegram. Você descreve um gasto em linguagem natural e ele salva na planilha. Depois é só pedir o resumo.

---

## Primeiros passos

### 1. Descubra seu ID do Telegram

Seu ID é um número único que identifica você no Telegram. O bot usa esse número para saber quem está autorizado a usá-lo.

1. Abra o Telegram e pesquise por **@userinfobot**
2. Clique em **Start**
3. O bot responde imediatamente com seu **User ID** (ex: `123456789`)
4. Anote esse número — você vai precisar dele na configuração

> Peça para cada pessoa que vai usar o bot fazer o mesmo e te mandar o ID.

---

### 2. Configure o arquivo `.env`

Copie o arquivo `.env.example` para `.env` e preencha:

```
TELEGRAM_TOKEN_BOTFATHER=seu_token_aqui
AUTHORIZED_USER_IDS=123456789,987654321
USER_NAMES=123456789:Mauricio,987654321:Ana
LLM_API_KEY=sua_chave_openrouter
GOOGLE_SHEET_NAME=MensagensBot
```

**Onde obter cada valor:**

| Variável | Como obter |
|---|---|
| `TELEGRAM_TOKEN_BOTFATHER` | Converse com [@BotFather](https://t.me/BotFather) no Telegram → `/newbot` |
| `AUTHORIZED_USER_IDS` | IDs obtidos no passo 1, separados por vírgula |
| `USER_NAMES` | Opcional — nomes que aparecem nos relatórios. Formato: `ID:Nome` |
| `LLM_API_KEY` | Crie uma conta em [openrouter.ai](https://openrouter.ai) → API Keys |
| `GOOGLE_SHEET_NAME` | Nome exato da sua planilha no Google Sheets (não é a URL) |

---

### 3. Configure o Google Sheets

O bot salva tudo numa planilha do Google. Para funcionar, a planilha precisa ser compartilhada com a conta de serviço do projeto:

1. Abra sua planilha no Google Sheets
2. Clique em **Compartilhar** (botão verde, canto superior direito)
3. Adicione o e-mail: `don-927@don-meu-agente.iam.gserviceaccount.com`
4. Dê permissão de **Editor**
5. Clique em **Enviar**

> O bot cria os cabeçalhos automaticamente na primeira execução. Não precisa criar nada manualmente.

---

### 4. Instale as dependências e rode

```bash
pip install -r requirements.txt
python main.py
```

---

## Adicionar um novo usuário

### 1. Encontre o bot no Telegram

O bot é identificado pelo username que você definiu no @BotFather. Para compartilhar:

- Link direto: `t.me/nome_do_seu_bot`
- Ou pesquisar `@nome_do_seu_bot` na busca do Telegram

### 2. Obtenha o ID do novo usuário

A pessoa precisa descobrir o próprio ID:

1. Abrir o Telegram e pesquisar **@userinfobot**
2. Clicar em **Start**
3. O bot responde com o **User ID** numérico (ex: `987654321`)
4. Passar esse número para você

> Enquanto o ID não estiver autorizado, o bot responde com `❌ Acesso não autorizado` para qualquer mensagem.

### 3. Autorize o novo usuário no `.env`

Adicione o ID e o nome nas variáveis correspondentes:

```
AUTHORIZED_USER_IDS=123456789,987654321
USER_NAMES=123456789:Mauricio,987654321:Ana
```

### 4. Reinicie o bot

As variáveis são lidas na inicialização — um restart é necessário para o acesso ser liberado.

- **Local:** pare o processo (`Ctrl+C`) e rode `python main.py` novamente
- **Railway:** vá em **Deployments** → **Redeploy**

---

## Como usar o bot

### Iniciando pela primeira vez

Abra o bot no Telegram e mande `/start`. Ele responde com uma mensagem de boas-vindas e aparece um **teclado fixo** na parte de baixo da tela com 3 botões:

```
[ 💰 Gastos ]  [ 📎 Comprovantes ]  [ ❓ Ajuda ]
```

Esses botões ficam sempre visíveis — é a forma mais rápida de navegar.

---

### Registrar um gasto

Basta digitar em linguagem natural:

```
Almoço 35 reais
Netflix 45,90
Uber 18
Farmácia 62,50 saúde
```

O bot identifica o valor, categoria e data automaticamente e confirma:

```
✅ Gasto registrado!
💰 R$ 35,00 — Almoço
📂 Alimentação | 📅 2026-05-12
```

---

### Registrar com comprovante (foto)

Envie uma **foto** com uma **legenda** descrevendo o gasto:

- Foto da nota fiscal + legenda: `Mercado 230 reais`
- Foto do boleto + legenda: `Condomínio 850`

O bot salva a foto junto com o lançamento e você pode recuperá-la depois pelo `/comprovante`.

---

### Ver resumo de gastos

Toque em **💰 Gastos** ou digite `/gastos`. O bot pergunta em dois passos:

**Passo 1 — Quem:**
```
[ 👤 Meus ]  [ 👥 Todos ]
[ 🔍 Por pessoa ]
```

**Passo 2 — Período:**
```
[ 📅 Mês atual (2026-05) ]
[ ⬅️ Mês passado (2026-04) ]
[ 📆 Este ano (2026) ]
```

O resultado mostra o total, número de lançamentos e breakdown por categoria:

```
📊 Gastos de Mauricio — 2026-05

💰 Total: R$ 1.250,00
🔢 Lançamentos: 18

📂 Por categoria:
  Alimentação: R$ 420,00
  Moradia: R$ 380,00
  Transporte: R$ 210,00
  ...
```

Abaixo do resumo aparece o botão **📋 Ver lançamentos** para ver cada gasto individualmente.

> **Atalho:** `/gastos 2026-05` pula a seleção de período e vai direto para "quem você quer ver?".

---

### Ver comprovantes

Toque em **📎 Comprovantes** ou digite `/comprovante`. Mesmo fluxo de botões do gastos. Depois de escolher quem e o período, o bot envia as fotos dos últimos 5 comprovantes encontrados.

---

### Consultas em linguagem natural

Além dos botões, você pode digitar livremente:

| O que você digita | O que o bot faz |
|---|---|
| `Quanto gastei esse mês?` | Abre o resumo de gastos |
| `Resumo de abril` | Abre o resumo de abril |
| `Mostra meus comprovantes de maio` | Abre comprovantes de maio |
| `O que você faz?` | Mostra o menu de ajuda |

---

## Categorias disponíveis

O bot classifica automaticamente nas categorias:

`Alimentação` · `Transporte` · `Moradia` · `Saúde` · `Lazer` · `Educação` · `Streaming` · `Roupas` · `Outros`

---

## Deploy no Railway

1. Faça push do projeto para um repositório no GitHub
2. Crie um projeto no [Railway](https://railway.app) a partir do repositório
3. Em **Variables**, adicione todas as variáveis do `.env`
4. Para `GOOGLE_CREDENTIALS_JSON`, cole o conteúdo completo do arquivo `google/*.json` numa única linha
5. O Railway detecta `main.py` e sobe automaticamente

Custo estimado: **~$5/mês** (mínimo do plano Hobby — o consumo real do bot fica bem abaixo disso).

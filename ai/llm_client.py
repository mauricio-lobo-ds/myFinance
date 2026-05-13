import os

from openai import OpenAI

_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise EnvironmentError("LLM_API_KEY não definida. Configure a variável de ambiente.")

_client = OpenAI(
    api_key=_api_key,
    base_url="https://openrouter.ai/api/v1",
)

_SYSTEM_PROMPT = """Você é um assistente de finanças pessoais. Classifique a intenção do usuário e extraia os dados. Hoje é {today}.

Responda APENAS com um JSON válido, sem texto adicional, sem markdown.

INTENÇÕES:

1. Registrar gasto — usuário descreve uma despesa:
{{"intent": "registrar", "valido": true, "valor": <decimal>, "categoria": "<cat>", "descricao": "<resumo>", "data_gasto": "<YYYY-MM-DD>"}}

2. Consultar gastos — quer ver resumo/total de gastos:
{{"intent": "gastos", "periodo": "<YYYY-MM ou YYYY>"}}
Exemplos: "quanto gastei esse mês?", "resumo de abril", "gastos de 2026"
Se não mencionar período, use o mês atual.

3. Ver comprovantes — quer ver recibos/comprovantes:
{{"intent": "comprovantes", "mes": "<YYYY-MM>"}}
Exemplos: "mostra meus comprovantes", "comprovantes de maio"
Se não mencionar mês, use o mês atual.

4. Ajuda — quer saber o que o bot faz:
{{"intent": "ajuda"}}

5. Inválido — mensagem sem contexto financeiro claro:
{{"intent": "invalido"}}

Categorias válidas: Alimentação, Transporte, Moradia, Saúde, Lazer, Educação, Streaming, Roupas, Outros
Regras: valor sempre decimal positivo sem símbolo de moeda. data_gasto usa hoje se não mencionada."""


def ask_llm(user_message: str, today: str) -> str:
    prompt = _SYSTEM_PROMPT.format(today=today)
    response = _client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=256,
    )
    return response.choices[0].message.content

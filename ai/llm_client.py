from openai import OpenAI
from config import LLM_API_KEY

_client = OpenAI(
    api_key=LLM_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

_SYSTEM_PROMPT = """Você é um assistente de finanças pessoais. O usuário vai te mandar mensagens descrevendo gastos.

Se a mensagem NÃO descrever um gasto (ex: saudações, perguntas, textos aleatórios, comandos), responda SOMENTE:
{"valido": false}

Se a mensagem descrever um gasto, extraia as informações e responda SOMENTE com um JSON válido no formato:
{"valido": true, "valor": <número decimal>, "categoria": "<categoria>", "descricao": "<descricao curta>", "data_gasto": "<YYYY-MM-DD>"}

Categorias possíveis: Alimentação, Transporte, Moradia, Saúde, Lazer, Educação, Streaming, Roupas, Outros

Regras:
- valor: sempre número decimal positivo (ex: 35.90), sem símbolo de moeda
- data_gasto: use a data de hoje se não for mencionada
- descricao: resumo curto do gasto
- Responda APENAS o JSON, sem texto adicional, sem markdown, sem explicações"""


def ask_llm(user_message: str, today: str) -> str:
    prompt = _SYSTEM_PROMPT.replace("a data de hoje", f"a data de hoje ({today})")
    response = _client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=256,
    )
    return response.choices[0].message.content

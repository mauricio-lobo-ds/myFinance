from openai import OpenAI
from config import LLM_API_KEY

_client = OpenAI(
    api_key=LLM_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

_SYSTEM_PROMPT = """Você é um assistente de finanças pessoais. Classifique a intenção do usuário e extraia os dados. Hoje é {today}.

Responda APENAS com um JSON válido, sem texto adicional, sem markdown.

INTENÇÕES:

1. Registrar gasto — usuário descreve uma despesa:
{{"intent": "registrar", "valido": true, "valor": <decimal>, "categoria": "<cat>", "descricao": "<resumo>", "data_gasto": "<YYYY-MM-DD>"}}

2. Consultar gastos — quer ver resumo/total de gastos:
{{"intent": "gastos", "periodo": "<YYYY-MM ou YYYY>", "who": "<meu|todos>", "categoria": "<categoria ou null>"}}
Exemplos: "quanto gastei esse mês?" -> who: meu, categoria: null. "gastos de todo mundo hoje" -> who: todos. "gastos com alimentação" -> categoria: "Alimentação". "quanto gastei em transporte em abril" -> categoria: "Transporte", periodo: "2026-04".
Se não mencionar período, use o mês atual. Se não mencionar de quem, use "meu". Se não mencionar categoria, use null.

3. Ver comprovantes — quer ver recibos/comprovantes:
{{"intent": "comprovantes", "mes": "<YYYY-MM>"}}
Exemplos: "mostra meus comprovantes", "comprovantes de maio"
Se não mencionar mês, use o mês atual.

4. Ajuda — quer saber o que o bot faz:
{{"intent": "ajuda"}}

5. Inválido — mensagem sem contexto financeiro claro:
{{"intent": "invalido"}}

Categorias válidas: Mercado, Alimentação, Transporte, Moradia (inclui água, luz, internet, aluguel, condominio, etc.), Saúde (planos de saude, medicos, consultas, remedios, etc.), Lazer, Educação, Assinaturas e Streamings (Telefone, Netflix, Spotify, Inteligencia Artificial, Storage em Nuvem etc.), Compras (roupas, objetos diversos para casa como microondas maquina de lavar e outros que nao sejam despesas regulares da moradia, camera fotografica, presentes, etc.), Besteiras (doces, superfluos, etc), Outros.
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

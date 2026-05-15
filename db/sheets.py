import json
import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_SHEET_NAME

_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

_creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if _creds_json:
    _creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(_creds_json), _SCOPES)
else:
    _creds = ServiceAccountCredentials.from_json_keyfile_name(
        "google/don-meu-agente-6886231ffdfe.json", _SCOPES
    )

_client = gspread.authorize(_creds)
_sheet = _client.open(GOOGLE_SHEET_NAME).sheet1

_HEADERS = ["timestamp", "user_id", "username", "mensagem_original",
            "valor", "categoria", "descricao", "data_gasto", "telegram_file_id", "tipo_gasto"]

def _ensure_headers() -> None:
    existing = _sheet.row_values(1)
    for i, header in enumerate(_HEADERS, start=1):
        if i > len(existing) or existing[i - 1] != header:
            _sheet.update_cell(1, i, header)

_ensure_headers()


def _safe_float(v) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return 0.0
    # Formato BR (1.234,56): remove pontos de milhar, troca vírgula decimal por ponto
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _normalize(rows: list[dict]) -> list[dict]:
    for r in rows:
        r["valor"] = _safe_float(r.get("valor", 0))
    return rows


def save_to_db(data: dict) -> None:
    _sheet.append_row([
        data["timestamp"],
        data["user_id"],
        data["username"],
        data["mensagem_original"],
        f"{_safe_float(data.get('valor', 0)):.2f}",
        data["categoria"],
        data["descricao"],
        data["data_gasto"],
        data.get("telegram_file_id", ""),
        data.get("tipo_gasto", ""),
    ])


def get_gastos(user_id: int, periodo: str = None, categoria: str = None, tipo_gasto: str = None) -> list[dict]:
    rows = _normalize(_sheet.get_all_records())
    return [
        r for r in rows
        if str(r.get("user_id")) == str(user_id)
        and (periodo is None or str(r.get("data_gasto", "")).startswith(periodo))
        and (categoria is None or r.get("categoria") == categoria)
        and (tipo_gasto is None or r.get("tipo_gasto") == tipo_gasto)
    ]


def get_gastos_todos(periodo: str = None, categoria: str = None, tipo_gasto: str = None) -> list[dict]:
    rows = _normalize(_sheet.get_all_records())
    return [
        r for r in rows
        if (periodo is None or str(r.get("data_gasto", "")).startswith(periodo))
        and (categoria is None or r.get("categoria") == categoria)
        and (tipo_gasto is None or r.get("tipo_gasto") == tipo_gasto)
    ]


def get_comprovantes_todos(mes: str = None) -> list[dict]:
    rows = _normalize(_sheet.get_all_records())
    return [
        r for r in rows
        if r.get("telegram_file_id")
        and (mes is None or str(r.get("data_gasto", "")).startswith(mes))
    ]


def get_comprovantes(user_id: int, mes: str = None) -> list[dict]:
    rows = _normalize(_sheet.get_all_records())
    return [
        r for r in rows
        if str(r.get("user_id")) == str(user_id)
        and r.get("telegram_file_id")
        and (mes is None or str(r.get("data_gasto", "")).startswith(mes))
    ]

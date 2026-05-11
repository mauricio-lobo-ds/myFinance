import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_SHEET_NAME

_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
_CREDENTIALS_FILE = "google/don-meu-agente-6886231ffdfe.json"

_creds = ServiceAccountCredentials.from_json_keyfile_name(_CREDENTIALS_FILE, _SCOPES)
_client = gspread.authorize(_creds)
_sheet = _client.open(GOOGLE_SHEET_NAME).sheet1


def save_to_db(data: dict) -> None:
    _sheet.append_row([
        data["timestamp"],
        data["user_id"],
        data["username"],
        data["mensagem_original"],
        data["valor"],
        data["categoria"],
        data["descricao"],
        data["data_gasto"],
    ])

import os
import sys
from unittest.mock import MagicMock

os.environ.setdefault("TELEGRAM_TOKEN_BOTFATHER", "test_token")
os.environ.setdefault("LLM_API_KEY", "test_key")
os.environ.setdefault("GOOGLE_SHEET_NAME", "TestSheet")
os.environ.setdefault("AUTHORIZED_USER_IDS", "123,456")

mock_sheet = MagicMock()
mock_sheet.row_values.return_value = [
    "timestamp", "user_id", "username", "mensagem_original",
    "valor", "categoria", "descricao", "data_gasto", "telegram_file_id",
]

mock_gspread = MagicMock()
mock_gspread.authorize.return_value.open.return_value.sheet1 = mock_sheet
sys.modules["gspread"] = mock_gspread

mock_oauth = MagicMock()
sys.modules["oauth2client"] = mock_oauth
sys.modules["oauth2client.service_account"] = mock_oauth.service_account

sys.modules["openai"] = MagicMock()
sys.modules["telebot"] = MagicMock()

import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_BOTFATHER")
LLM_API_KEY = os.getenv("LLM_API_KEY")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "MensagensBot")

_raw_ids = os.getenv("AUTHORIZED_USER_IDS", "")
AUTHORIZED_USER_IDS = [int(uid.strip()) for uid in _raw_ids.split(",") if uid.strip()]

import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_BOTFATHER")
LLM_API_KEY = os.getenv("LLM_API_KEY")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "MensagensBot")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

_raw_ids = os.getenv("AUTHORIZED_USER_IDS", "")
AUTHORIZED_USER_IDS = [int(uid.strip()) for uid in _raw_ids.split(",") if uid.strip()]

# USER_NAMES=111:Mauricio,222:Ana
_raw_names = os.getenv("USER_NAMES", "")
USER_NAMES: dict[int, str] = {}
for _entry in _raw_names.split(","):
    if ":" in _entry:
        _uid, _name = _entry.split(":", 1)
        try:
            USER_NAMES[int(_uid.strip())] = _name.strip()
        except ValueError:
            pass

import os
print("[DEBUG] LLM_API_KEY present:", bool(os.getenv("LLM_API_KEY")), flush=True)
print("[DEBUG] OPENAI_API_KEY present:", bool(os.getenv("OPENAI_API_KEY")), flush=True)
print("[DEBUG] TELEGRAM present:", bool(os.getenv("TELEGRAM_TOKEN_BOTFATHER")), flush=True)

import telebot
from config import TELEGRAM_TOKEN
from handlers.message_handler import register_handlers

bot = telebot.TeleBot(TELEGRAM_TOKEN)
register_handlers(bot)

if __name__ == "__main__":
    print("Bot iniciado. Aguardando mensagens...")
    bot.infinity_polling()

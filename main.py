import telebot
from config import TELEGRAM_TOKEN
from handlers.message_handler import register_handlers

bot = telebot.TeleBot(TELEGRAM_TOKEN)
register_handlers(bot)

if __name__ == "__main__":
    print("Bot iniciado. Aguardando mensagens...")
    bot.infinity_polling()

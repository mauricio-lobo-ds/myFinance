import json
from datetime import datetime
import telebot
from handlers.auth import is_authorized
from ai.llm_client import ask_llm
from db.sheets import save_to_db


def register_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(func=lambda m: True)
    def handle_message(message: telebot.types.Message) -> None:
        user_id = message.from_user.id

        if not is_authorized(user_id):
            bot.reply_to(message, "❌ Acesso não autorizado.")
            return

        today = datetime.now().strftime("%Y-%m-%d")
        raw = ask_llm(message.text, today)

        try:
            expense = json.loads(raw)
        except json.JSONDecodeError:
            bot.reply_to(message, "❌ Não entendi o gasto. Tente algo como: 'Almoço 35 reais' ou 'Gasolina 120'.")
            return

        if not expense.get("valido", False):
            bot.reply_to(message, "ℹ️ Manda um gasto pra eu registrar! Ex: 'Almoço 35 reais' ou 'Netflix 45,90'.")
            return

        save_to_db({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": message.from_user.username or "",
            "mensagem_original": message.text,
            "valor": expense.get("valor", 0),
            "categoria": expense.get("categoria", "Outros"),
            "descricao": expense.get("descricao", ""),
            "data_gasto": expense.get("data_gasto", today),
        })

        reply = (
            f"✅ Gasto registrado!\n"
            f"💰 R$ {expense.get('valor', 0):.2f} — {expense.get('descricao', '')}\n"
            f"📂 {expense.get('categoria', 'Outros')} | 📅 {expense.get('data_gasto', today)}"
        )
        bot.reply_to(message, reply)

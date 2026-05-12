import json
from datetime import datetime
import telebot
from handlers.auth import is_authorized
from ai.llm_client import ask_llm
from db.sheets import save_to_db, get_comprovantes, get_gastos


def register_handlers(bot: telebot.TeleBot) -> None:

    def _classify(text: str, today: str) -> dict | None:
        raw = ask_llm(text, today)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def _build_reply(expense: dict, today: str, com_comprovante: bool = False) -> str:
        return (
            f"✅ Gasto registrado{'  com comprovante' if com_comprovante else ''}!\n"
            f"💰 R$ {expense.get('valor', 0):.2f} — {expense.get('descricao', '')}\n"
            f"📂 {expense.get('categoria', 'Outros')} | 📅 {expense.get('data_gasto', today)}"
        )

    @bot.message_handler(commands=["help", "ajuda"])
    def handle_help(message: telebot.types.Message) -> None:
        if not is_authorized(message.from_user.id):
            bot.reply_to(message, "❌ Acesso não autorizado.")
            return

        texto = (
            "🤖 *Comandos disponíveis*\n\n"
            "*Registrar gasto*\n"
            "Basta enviar uma mensagem descrevendo o gasto:\n"
            "`Almoço 35 reais`\n"
            "`Netflix 45,90 streaming`\n\n"
            "*Registrar com comprovante*\n"
            "Envie uma foto com legenda descrevendo o gasto:\n"
            "`[foto] Condomínio 850`\n\n"
            "*Resumo de gastos*\n"
            "/gastos — resumo do mês atual\n"
            "/gastos 2026\\-05 — resumo de maio/2026\n"
            "/gastos 2026 — resumo do ano\n\n"
            "*Comprovantes*\n"
            "/comprovante — últimos 5 comprovantes\n"
            "/comprovante 2026\\-05 — comprovantes de maio/2026\n\n"
            "*Ajuda*\n"
            "/help — exibe esta mensagem"
        )
        bot.reply_to(message, texto, parse_mode="MarkdownV2")

    @bot.message_handler(commands=["gastos"])
    def handle_gastos(message: telebot.types.Message) -> None:
        user_id = message.from_user.id

        if not is_authorized(user_id):
            bot.reply_to(message, "❌ Acesso não autorizado.")
            return

        args = message.text.split(maxsplit=1)
        periodo = args[1].strip() if len(args) > 1 else datetime.now().strftime("%Y-%m")

        rows = get_gastos(user_id, periodo)

        if not rows:
            bot.reply_to(message, f"ℹ️ Nenhum gasto encontrado para {periodo}.")
            return

        total = sum(float(r.get("valor", 0)) for r in rows)

        por_categoria: dict[str, float] = {}
        for r in rows:
            cat = r.get("categoria", "Outros")
            por_categoria[cat] = por_categoria.get(cat, 0) + float(r.get("valor", 0))

        linhas_cat = "\n".join(
            f"  {cat}: R$ {valor:.2f}"
            for cat, valor in sorted(por_categoria.items(), key=lambda x: -x[1])
        )

        texto = (
            f"📊 Gastos de {periodo}\n\n"
            f"💰 Total: R$ {total:.2f}\n"
            f"🔢 Lançamentos: {len(rows)}\n\n"
            f"📂 Por categoria:\n{linhas_cat}"
        )
        bot.reply_to(message, texto)

    @bot.message_handler(commands=["comprovante"])
    def handle_comprovante(message: telebot.types.Message) -> None:
        user_id = message.from_user.id

        if not is_authorized(user_id):
            bot.reply_to(message, "❌ Acesso não autorizado.")
            return

        args = message.text.split(maxsplit=1)
        mes = args[1].strip() if len(args) > 1 else None

        resultados = get_comprovantes(user_id, mes)

        if not resultados:
            dica = f" para {mes}" if mes else ""
            bot.reply_to(message, f"ℹ️ Nenhum comprovante encontrado{dica}.")
            return

        for r in resultados[-5:]:
            caption = (
                f"💰 R$ {float(r.get('valor', 0)):.2f} — {r.get('descricao', '')}\n"
                f"📂 {r.get('categoria', '')} | 📅 {r.get('data_gasto', '')}"
            )
            bot.send_photo(message.chat.id, r["telegram_file_id"], caption=caption)

    @bot.message_handler(content_types=["photo"])
    def handle_photo(message: telebot.types.Message) -> None:
        user_id = message.from_user.id

        if not is_authorized(user_id):
            bot.reply_to(message, "❌ Acesso não autorizado.")
            return

        caption = message.caption
        if not caption:
            bot.reply_to(message, "📎 Mande a foto com uma legenda descrevendo o gasto. Ex: 'Condomínio 850'")
            return

        today = datetime.now().strftime("%Y-%m-%d")
        expense = _classify(caption, today)

        if expense is None or expense.get("intent") != "registrar" or not expense.get("valido", False):
            bot.reply_to(message, "❌ Não entendi o gasto na legenda. Tente: 'Condomínio 850 reais'.")
            return

        file_id = message.photo[-1].file_id

        save_to_db({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": message.from_user.username or "",
            "mensagem_original": caption,
            "valor": expense.get("valor", 0),
            "categoria": expense.get("categoria", "Outros"),
            "descricao": expense.get("descricao", ""),
            "data_gasto": expense.get("data_gasto", today),
            "telegram_file_id": file_id,
        })

        bot.reply_to(message, _build_reply(expense, today, com_comprovante=True))

    @bot.message_handler(func=lambda m: True)
    def handle_message(message: telebot.types.Message) -> None:
        user_id = message.from_user.id

        if not is_authorized(user_id):
            bot.reply_to(message, "❌ Acesso não autorizado.")
            return

        today = datetime.now().strftime("%Y-%m-%d")
        resultado = _classify(message.text, today)

        if resultado is None:
            bot.reply_to(message, "❌ Não consegui entender. Tente novamente ou use /help.")
            return

        intent = resultado.get("intent")

        if intent == "registrar":
            if not resultado.get("valido", False):
                bot.reply_to(message, "ℹ️ Manda um gasto pra eu registrar! Ex: 'Almoço 35 reais' ou 'Netflix 45,90'.")
                return
            save_to_db({
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "username": message.from_user.username or "",
                "mensagem_original": message.text,
                "valor": resultado.get("valor", 0),
                "categoria": resultado.get("categoria", "Outros"),
                "descricao": resultado.get("descricao", ""),
                "data_gasto": resultado.get("data_gasto", today),
            })
            bot.reply_to(message, _build_reply(resultado, today))

        elif intent == "gastos":
            periodo = resultado.get("periodo", today[:7])
            rows = get_gastos(user_id, periodo)
            if not rows:
                bot.reply_to(message, f"ℹ️ Nenhum gasto encontrado para {periodo}.")
                return
            total = sum(float(r.get("valor", 0)) for r in rows)
            por_categoria: dict[str, float] = {}
            for r in rows:
                cat = r.get("categoria", "Outros")
                por_categoria[cat] = por_categoria.get(cat, 0) + float(r.get("valor", 0))
            linhas_cat = "\n".join(
                f"  {cat}: R$ {valor:.2f}"
                for cat, valor in sorted(por_categoria.items(), key=lambda x: -x[1])
            )
            bot.reply_to(message, (
                f"📊 Gastos de {periodo}\n\n"
                f"💰 Total: R$ {total:.2f}\n"
                f"🔢 Lançamentos: {len(rows)}\n\n"
                f"📂 Por categoria:\n{linhas_cat}"
            ))

        elif intent == "comprovantes":
            mes = resultado.get("mes", today[:7])
            resultados = get_comprovantes(user_id, mes)
            if not resultados:
                bot.reply_to(message, f"ℹ️ Nenhum comprovante encontrado para {mes}.")
                return
            for r in resultados[-5:]:
                caption = (
                    f"💰 R$ {r['valor']:.2f} — {r['descricao']}\n"
                    f"📂 {r['categoria']} | 📅 {r['data_gasto']}"
                )
                bot.send_photo(message.chat.id, r["telegram_file_id"], caption=caption)

        elif intent == "ajuda":
            handle_help(message)

        else:
            bot.reply_to(message, "ℹ️ Não entendi. Use /help para ver o que posso fazer.")


import json
from datetime import datetime, timedelta
import telebot
from handlers.auth import is_authorized
from ai.llm_client import ask_llm
from db.sheets import save_to_db, get_comprovantes, get_comprovantes_todos, get_gastos, get_gastos_todos
from config import USER_NAMES, AUTHORIZED_USER_IDS

# (chat_id, bot_message_id) -> {"periodo": str|None, "who": str, "target_uid": int, "requesting_user_id": int}
_gastos_state: dict[tuple[int, int], dict] = {}
_comp_state: dict[tuple[int, int], dict] = {}
_pending_expense: dict[tuple[int, int], dict] = {}
_editing_state: dict[tuple[int, int], dict] = {}
_chat_bot_msgs: dict[int, list[int]] = {}


_QUICK_ACTIONS = {"💸", "📎", "❓", "🧹"}
_CATEGORIES = ["Alimentação", "Transporte", "Moradia", "Saúde", "Lazer", "Educação", "Streaming", "Roupas", "Outros"]


def _track_msg(chat_id: int, message_id: int) -> None:
    msgs = _chat_bot_msgs.setdefault(chat_id, [])
    msgs.append(message_id)
    if len(msgs) > 100:
        msgs.pop(0)


def _reply_keyboard() -> telebot.types.ReplyKeyboardMarkup:
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(
        telebot.types.KeyboardButton("💸"),
        telebot.types.KeyboardButton("📎"),
        telebot.types.KeyboardButton("❓"),
        telebot.types.KeyboardButton("🧹"),
    )
    return kb


def _nome_usuario(uid: int, username: str = "") -> str:
    return USER_NAMES.get(uid) or (f"@{username}" if username else f"ID {uid}")


def _keyboard_who(prefix: str = "gastos") -> telebot.types.InlineKeyboardMarkup:
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        telebot.types.InlineKeyboardButton("👤 Meus", callback_data=f"{prefix}:who:meu"),
        telebot.types.InlineKeyboardButton("👥 Todos", callback_data=f"{prefix}:who:todos"),
    )
    kb.add(telebot.types.InlineKeyboardButton("🔍 Por pessoa", callback_data=f"{prefix}:who:pessoa"))
    return kb


def _keyboard_period(prefix: str = "gastos") -> telebot.types.InlineKeyboardMarkup:
    now = datetime.now()
    mes_atual = now.strftime("%Y-%m")
    mes_anterior = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    ano_atual = now.strftime("%Y")
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton(f"📅 Mês atual ({mes_atual})", callback_data=f"{prefix}:period:{mes_atual}"))
    kb.add(telebot.types.InlineKeyboardButton(f"⬅️ Mês passado ({mes_anterior})", callback_data=f"{prefix}:period:{mes_anterior}"))
    kb.add(telebot.types.InlineKeyboardButton(f"📆 Este ano ({ano_atual})", callback_data=f"{prefix}:period:{ano_atual}"))
    return kb


def _keyboard_pessoas(prefix: str = "gastos") -> telebot.types.InlineKeyboardMarkup:
    kb = telebot.types.InlineKeyboardMarkup()
    for uid in AUTHORIZED_USER_IDS:
        nome = USER_NAMES.get(uid, f"Usuário {uid}")
        kb.add(telebot.types.InlineKeyboardButton(nome, callback_data=f"{prefix}:uid:{uid}"))
    return kb


def _build_gastos_text(titulo: str, rows: list[dict], show_por_pessoa: bool = False) -> str:
    total = sum(float(r.get("valor", 0) or 0) for r in rows)
    parts = [f"📊 {titulo}\n", f"💰 Total: R$ {total:.2f}", f"🔢 Lançamentos: {len(rows)}"]

    if show_por_pessoa:
        por_usuario: dict[str, float] = {}
        for r in rows:
            try:
                uid = int(r.get("user_id", 0))
                nome = USER_NAMES.get(uid) or r.get("username") or str(uid)
            except (ValueError, TypeError):
                nome = r.get("username") or str(r.get("user_id", "?"))
            por_usuario[nome] = por_usuario.get(nome, 0) + float(r.get("valor", 0) or 0)
        parts.append("\n👥 Por pessoa:")
        for nome, valor in sorted(por_usuario.items(), key=lambda x: -x[1]):
            parts.append(f"  {nome}: R$ {valor:.2f}")

    por_categoria: dict[str, float] = {}
    for r in rows:
        cat = r.get("categoria", "Outros")
        por_categoria[cat] = por_categoria.get(cat, 0) + float(r.get("valor", 0) or 0)
    parts.append("\n📂 Por categoria:")
    for cat, valor in sorted(por_categoria.items(), key=lambda x: -x[1]):
        parts.append(f"  {cat}: R$ {valor:.2f}")

    return "\n".join(parts)


def _resolve_gastos(who: str, requesting_uid: int, target_uid: int | None, periodo: str) -> tuple[list[dict], str, bool]:
    if who == "todos":
        return get_gastos_todos(periodo), f"Todos os gastos — {periodo}", True
    if who == "uid" and target_uid is not None:
        nome = _nome_usuario(target_uid)
        return get_gastos(target_uid, periodo), f"Gastos de {nome} — {periodo}", False
    nome = _nome_usuario(requesting_uid)
    return get_gastos(requesting_uid, periodo), f"Gastos de {nome} — {periodo}", False


def _resolve_comprovantes(who: str, requesting_uid: int, target_uid: int | None, mes: str) -> tuple[list[dict], str]:
    if who == "todos":
        return get_comprovantes_todos(mes), f"Todos os comprovantes — {mes}"
    if who == "uid" and target_uid is not None:
        nome = _nome_usuario(target_uid)
        return get_comprovantes(target_uid, mes), f"Comprovantes de {nome} — {mes}"
    nome = _nome_usuario(requesting_uid)
    return get_comprovantes(requesting_uid, mes), f"Comprovantes de {nome} — {mes}"


def _keyboard_lancamentos(who: str, requesting_uid: int, target_uid: int | None, periodo: str) -> telebot.types.InlineKeyboardMarkup:
    tgt = str(target_uid) if target_uid else ""
    data = f"lanca:{who}:{requesting_uid}:{tgt}:{periodo}"
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton("📋 Ver lançamentos", callback_data=data))
    return kb


def _build_lancamentos_text(titulo: str, rows: list[dict], show_pessoa: bool = False) -> str:
    MAX = 30
    total = len(rows)
    exibidos = rows[-MAX:] if total > MAX else rows
    parts = [f"📋 {titulo}"]
    if total > MAX:
        parts.append(f"(mostrando os {MAX} mais recentes de {total})\n")
    else:
        parts.append("")
    for r in exibidos:
        data_gasto = r.get("data_gasto", "")
        desc = r.get("descricao") or r.get("mensagem_original", "")
        valor = float(r.get("valor", 0) or 0)
        cat = r.get("categoria", "Outros")
        linha = f"📅 {data_gasto}  💰 R$ {valor:.2f}\n  {desc} · {cat}"
        if show_pessoa:
            try:
                uid = int(r.get("user_id", 0))
                nome = USER_NAMES.get(uid) or r.get("username") or str(uid)
            except (ValueError, TypeError):
                nome = r.get("username") or "?"
            linha += f" · {nome}"
        parts.append(linha)
    return "\n".join(parts)


def _preview_text(expense: dict, com_comprovante: bool = False) -> str:
    comprovante_line = "\n📷 Com comprovante" if com_comprovante else ""
    return (
        f"📋 Confirma o registro?\n\n"
        f"💰 R$ {expense.get('valor', 0):.2f} — {expense.get('descricao', '')}\n"
        f"📂 {expense.get('categoria', 'Outros')} | 📅 {expense.get('data_gasto', '')}"
        f"{comprovante_line}"
    )


def _keyboard_confirm() -> telebot.types.InlineKeyboardMarkup:
    kb = telebot.types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        telebot.types.InlineKeyboardButton("✅", callback_data="pend:confirm"),
        telebot.types.InlineKeyboardButton("❌", callback_data="pend:cancel"),
        telebot.types.InlineKeyboardButton("✏️", callback_data="pend:edit"),
    )
    return kb


def _keyboard_edit_fields() -> telebot.types.InlineKeyboardMarkup:
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        telebot.types.InlineKeyboardButton("💰 Valor", callback_data="pend:field:valor"),
        telebot.types.InlineKeyboardButton("📂 Categoria", callback_data="pend:field:categoria"),
    )
    kb.add(
        telebot.types.InlineKeyboardButton("📝 Descrição", callback_data="pend:field:descricao"),
        telebot.types.InlineKeyboardButton("📅 Data", callback_data="pend:field:data"),
    )
    kb.add(telebot.types.InlineKeyboardButton("⬅️ Voltar", callback_data="pend:back"))
    return kb


def _keyboard_categories() -> telebot.types.InlineKeyboardMarkup:
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    for cat in _CATEGORIES:
        kb.add(telebot.types.InlineKeyboardButton(cat, callback_data=f"pend:cat:{cat}"))
    kb.add(telebot.types.InlineKeyboardButton("⬅️ Voltar", callback_data="pend:edit"))
    return kb


def register_handlers(bot: telebot.TeleBot) -> None:

    def _classify(text: str, today: str) -> dict | None:
        raw = ask_llm(text, today)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def _start_gastos_flow(message: telebot.types.Message, user_id: int, periodo: str | None) -> None:
        text = f"📊 Gastos de {periodo} — quem você quer ver?" if periodo else "📊 Gastos — o que você quer ver?"
        sent = bot.reply_to(message, text, reply_markup=_keyboard_who("gastos"))
        _track_msg(message.chat.id, sent.message_id)
        _gastos_state[(message.chat.id, sent.message_id)] = {
            "periodo": periodo,
            "requesting_user_id": user_id,
        }

    def _start_comp_flow(message: telebot.types.Message, user_id: int, mes: str | None) -> None:
        text = f"📎 Comprovantes de {mes} — quem você quer ver?" if mes else "📎 Comprovantes — o que você quer ver?"
        sent = bot.reply_to(message, text, reply_markup=_keyboard_who("comp"))
        _track_msg(message.chat.id, sent.message_id)
        _comp_state[(message.chat.id, sent.message_id)] = {
            "periodo": mes,
            "requesting_user_id": user_id,
        }

    @bot.message_handler(commands=["start"])
    def handle_start(message: telebot.types.Message) -> None:
        if not is_authorized(message.from_user.id):
            bot.reply_to(message, "❌ Acesso não autorizado.")
            return
        nome = message.from_user.first_name or "você"
        sent = bot.reply_to(
            message,
            f"👋 Olá, {nome}\\! Use os botões abaixo ou descreva um gasto para registrar\\.",
            parse_mode="MarkdownV2",
            reply_markup=_reply_keyboard(),
        )
        _track_msg(message.chat.id, sent.message_id)

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
            "/gastos — resumo interativo com filtros\n"
            "/gastos 2026\\-05 — gastos de maio/2026\n"
            "/gastos 2026 — gastos do ano\n\n"
            "*Comprovantes*\n"
            "/comprovante — últimos 5 comprovantes\n"
            "/comprovante 2026\\-05 — comprovantes de maio/2026\n\n"
            "*Ajuda*\n"
            "/help — exibe esta mensagem"
        )
        sent = bot.reply_to(message, texto, parse_mode="MarkdownV2", reply_markup=_reply_keyboard())
        _track_msg(message.chat.id, sent.message_id)

    @bot.message_handler(commands=["gastos"])
    def handle_gastos(message: telebot.types.Message) -> None:
        user_id = message.from_user.id
        if not is_authorized(user_id):
            bot.reply_to(message, "❌ Acesso não autorizado.")
            return
        args = message.text.split(maxsplit=1)
        periodo = args[1].strip() if len(args) > 1 else None
        _start_gastos_flow(message, user_id, periodo)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("gastos:"))
    def handle_gastos_callback(call: telebot.types.CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        state_key = (chat_id, msg_id)

        if not is_authorized(user_id):
            bot.answer_callback_query(call.id, "❌ Acesso não autorizado.")
            return

        state = _gastos_state.get(state_key, {})
        requesting_uid = state.get("requesting_user_id", user_id)
        data = call.data

        def _edit_result(who: str, req_uid: int, tgt_uid: int | None, periodo: str) -> None:
            rows, titulo, spp = _resolve_gastos(who, req_uid, tgt_uid, periodo)
            if not rows:
                bot.edit_message_text(f"ℹ️ Nenhum gasto encontrado para {periodo}.", chat_id, msg_id)
            else:
                kb = _keyboard_lancamentos(who, req_uid, tgt_uid, periodo)
                bot.edit_message_text(_build_gastos_text(titulo, rows, spp), chat_id, msg_id, reply_markup=kb)

        if data.startswith("gastos:who:"):
            who = data[len("gastos:who:"):]
            if who == "pessoa":
                _gastos_state[state_key] = {**state, "step": "pessoa"}
                bot.edit_message_text(
                    "🔍 Selecione a pessoa:",
                    chat_id, msg_id,
                    reply_markup=_keyboard_pessoas(),
                )
            else:
                periodo = state.get("periodo")
                _gastos_state[state_key] = {**state, "who": who}
                if periodo:
                    _gastos_state.pop(state_key, None)
                    _edit_result(who, requesting_uid, None, periodo)
                else:
                    bot.edit_message_text("📅 Qual período?", chat_id, msg_id, reply_markup=_keyboard_period())

        elif data.startswith("gastos:uid:"):
            target_uid = int(data[len("gastos:uid:"):])
            periodo = state.get("periodo")
            _gastos_state[state_key] = {**state, "who": "uid", "target_uid": target_uid}
            if periodo:
                _gastos_state.pop(state_key, None)
                _edit_result("uid", requesting_uid, target_uid, periodo)
            else:
                bot.edit_message_text("📅 Qual período?", chat_id, msg_id, reply_markup=_keyboard_period())

        elif data.startswith("gastos:period:"):
            periodo = data[len("gastos:period:"):]
            who = state.get("who", "meu")
            target_uid = state.get("target_uid")
            _gastos_state.pop(state_key, None)
            _edit_result(who, requesting_uid, target_uid, periodo)

        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("comp:"))
    def handle_comp_callback(call: telebot.types.CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        state_key = (chat_id, msg_id)

        if not is_authorized(user_id):
            bot.answer_callback_query(call.id, "❌ Acesso não autorizado.")
            return

        state = _comp_state.get(state_key, {})
        requesting_uid = state.get("requesting_user_id", user_id)
        data = call.data

        def _send_comp_result(who: str, req_uid: int, tgt_uid: int | None, mes: str) -> None:
            rows, titulo = _resolve_comprovantes(who, req_uid, tgt_uid, mes)
            if not rows:
                bot.edit_message_text(f"ℹ️ Nenhum comprovante encontrado para {mes}.", chat_id, msg_id)
                return
            bot.edit_message_text(f"📎 {titulo}\n{len(rows)} comprovante(s) encontrado(s):", chat_id, msg_id)
            for r in rows[-5:]:
                caption = (
                    f"💰 R$ {float(r.get('valor', 0)):.2f} — {r.get('descricao', '')}\n"
                    f"📂 {r.get('categoria', '')} | 📅 {r.get('data_gasto', '')}"
                )
                sent_photo = bot.send_photo(chat_id, r["telegram_file_id"], caption=caption)
                _track_msg(chat_id, sent_photo.message_id)

        if data.startswith("comp:who:"):
            who = data[len("comp:who:"):]
            if who == "pessoa":
                _comp_state[state_key] = {**state, "step": "pessoa"}
                bot.edit_message_text("🔍 Selecione a pessoa:", chat_id, msg_id, reply_markup=_keyboard_pessoas("comp"))
            else:
                mes = state.get("periodo")
                _comp_state[state_key] = {**state, "who": who}
                if mes:
                    _comp_state.pop(state_key, None)
                    _send_comp_result(who, requesting_uid, None, mes)
                else:
                    bot.edit_message_text("📅 Qual período?", chat_id, msg_id, reply_markup=_keyboard_period("comp"))

        elif data.startswith("comp:uid:"):
            target_uid = int(data[len("comp:uid:"):])
            mes = state.get("periodo")
            _comp_state[state_key] = {**state, "who": "uid", "target_uid": target_uid}
            if mes:
                _comp_state.pop(state_key, None)
                _send_comp_result("uid", requesting_uid, target_uid, mes)
            else:
                bot.edit_message_text("📅 Qual período?", chat_id, msg_id, reply_markup=_keyboard_period("comp"))

        elif data.startswith("comp:period:"):
            mes = data[len("comp:period:"):]
            who = state.get("who", "meu")
            target_uid = state.get("target_uid")
            _comp_state.pop(state_key, None)
            _send_comp_result(who, requesting_uid, target_uid, mes)

        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("lanca:"))
    def handle_lancamentos_callback(call: telebot.types.CallbackQuery) -> None:
        if not is_authorized(call.from_user.id):
            bot.answer_callback_query(call.id, "❌ Acesso não autorizado.")
            return

        _, who, req_uid_s, tgt_uid_s, periodo = call.data.split(":", 4)
        req_uid = int(req_uid_s)
        tgt_uid = int(tgt_uid_s) if tgt_uid_s else None

        rows, titulo, spp = _resolve_gastos(who, req_uid, tgt_uid, periodo)
        if not rows:
            bot.answer_callback_query(call.id, "Nenhum lançamento encontrado.")
            return

        texto = _build_lancamentos_text(titulo, rows, show_pessoa=spp)
        sent = bot.send_message(call.message.chat.id, texto)
        _track_msg(call.message.chat.id, sent.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("pend:"))
    def handle_pending_callback(call: telebot.types.CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        state_key = (chat_id, msg_id)

        if not is_authorized(user_id):
            bot.answer_callback_query(call.id, "❌ Acesso não autorizado.")
            return

        state = _pending_expense.get(state_key)
        if not state:
            bot.answer_callback_query(call.id, "⚠️ Registro expirado. Envie novamente.")
            bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
            return

        expense = state["expense"]
        data = call.data

        if data == "pend:confirm":
            save_to_db({
                "timestamp": datetime.now().isoformat(),
                "user_id": state["requesting_user_id"],
                "username": state.get("username", ""),
                "mensagem_original": state.get("mensagem_original", ""),
                "valor": expense.get("valor", 0),
                "categoria": expense.get("categoria", "Outros"),
                "descricao": expense.get("descricao", ""),
                "data_gasto": expense.get("data_gasto", ""),
                "telegram_file_id": state.get("telegram_file_id") or "",
            })
            _pending_expense.pop(state_key, None)
            com_comprovante = bool(state.get("telegram_file_id"))
            bot.edit_message_text(
                f"✅ Gasto registrado{'  com comprovante' if com_comprovante else ''}!\n"
                f"💰 R$ {expense.get('valor', 0):.2f} — {expense.get('descricao', '')}\n"
                f"📂 {expense.get('categoria', 'Outros')} | 📅 {expense.get('data_gasto', '')}",
                chat_id, msg_id,
            )
            sent = bot.send_message(chat_id, "💬 Mais alguma coisa?", reply_markup=_reply_keyboard())
            _track_msg(chat_id, sent.message_id)

        elif data == "pend:cancel":
            _pending_expense.pop(state_key, None)
            bot.edit_message_text("❌ Registro cancelado.", chat_id, msg_id)
            sent = bot.send_message(chat_id, "💬 Pode mandar outro gasto.", reply_markup=_reply_keyboard())
            _track_msg(chat_id, sent.message_id)

        elif data == "pend:edit":
            bot.edit_message_text(
                f"✏️ O que você quer editar?\n\n"
                f"💰 R$ {expense.get('valor', 0):.2f} — {expense.get('descricao', '')}\n"
                f"📂 {expense.get('categoria', 'Outros')} | 📅 {expense.get('data_gasto', '')}",
                chat_id, msg_id,
                reply_markup=_keyboard_edit_fields(),
            )

        elif data == "pend:back":
            com_comprovante = bool(state.get("telegram_file_id"))
            bot.edit_message_text(
                _preview_text(expense, com_comprovante),
                chat_id, msg_id,
                reply_markup=_keyboard_confirm(),
            )

        elif data.startswith("pend:field:"):
            field = data[len("pend:field:"):]
            if field == "categoria":
                bot.edit_message_text("📂 Selecione a categoria:", chat_id, msg_id, reply_markup=_keyboard_categories())
            else:
                prompts = {
                    "valor": "Qual o novo valor? (ex: 35.90)",
                    "descricao": "Qual a nova descrição?",
                    "data": "Qual a nova data? (ex: 2026-05-13)",
                }
                _editing_state[(chat_id, user_id)] = {"field": field, "confirm_msg_id": msg_id}
                bot.edit_message_text(prompts.get(field, f"Digite o novo {field}:"), chat_id, msg_id)

        elif data.startswith("pend:cat:"):
            cat = data[len("pend:cat:"):]
            state["expense"]["categoria"] = cat
            com_comprovante = bool(state.get("telegram_file_id"))
            bot.edit_message_text(
                _preview_text(expense, com_comprovante),
                chat_id, msg_id,
                reply_markup=_keyboard_confirm(),
            )

        bot.answer_callback_query(call.id)

    @bot.message_handler(commands=["comprovante"])
    def handle_comprovante(message: telebot.types.Message) -> None:
        user_id = message.from_user.id
        if not is_authorized(user_id):
            bot.reply_to(message, "❌ Acesso não autorizado.")
            return
        args = message.text.split(maxsplit=1)
        mes = args[1].strip() if len(args) > 1 else None
        _start_comp_flow(message, user_id, mes)

    @bot.message_handler(content_types=["photo"])
    def handle_photo(message: telebot.types.Message) -> None:
        user_id = message.from_user.id
        if not is_authorized(user_id):
            bot.reply_to(message, "❌ Acesso não autorizado.")
            return
        caption = message.caption
        if not caption:
            sent = bot.reply_to(message, "📎 Mande a foto com uma legenda descrevendo o gasto. Ex: 'Condomínio 850'", reply_markup=_reply_keyboard())
            _track_msg(message.chat.id, sent.message_id)
            return
        today = datetime.now().strftime("%Y-%m-%d")
        classified = _classify(caption, today)
        if classified is None or classified.get("intent") != "registrar" or not classified.get("valido", False):
            sent = bot.reply_to(message, "❌ Não entendi o gasto na legenda. Tente: 'Condomínio 850 reais'.", reply_markup=_reply_keyboard())
            _track_msg(message.chat.id, sent.message_id)
            return
        file_id = message.photo[-1].file_id
        expense = {
            "valor": classified.get("valor", 0),
            "categoria": classified.get("categoria", "Outros"),
            "descricao": classified.get("descricao", ""),
            "data_gasto": classified.get("data_gasto", today),
        }
        sent = bot.reply_to(message, _preview_text(expense, com_comprovante=True), reply_markup=_keyboard_confirm())
        _track_msg(message.chat.id, sent.message_id)
        _pending_expense[(message.chat.id, sent.message_id)] = {
            "expense": expense,
            "requesting_user_id": user_id,
            "username": message.from_user.username or "",
            "mensagem_original": caption,
            "telegram_file_id": file_id,
        }

    @bot.message_handler(func=lambda m: True)
    def handle_message(message: telebot.types.Message) -> None:
        user_id = message.from_user.id
        if not is_authorized(user_id):
            bot.reply_to(message, "❌ Acesso não autorizado.")
            return

        chat_id = message.chat.id
        edit_info = _editing_state.pop((chat_id, user_id), None)
        if edit_info:
            confirm_msg_id = edit_info["confirm_msg_id"]
            state_key = (chat_id, confirm_msg_id)
            state = _pending_expense.get(state_key)
            if state:
                field = edit_info["field"]
                expense = state["expense"]
                if field == "valor":
                    try:
                        expense["valor"] = float(message.text.replace(",", "."))
                    except ValueError:
                        sent = bot.reply_to(message, "❌ Valor inválido. Ex: 35.90")
                        _track_msg(chat_id, sent.message_id)
                        _editing_state[(chat_id, user_id)] = edit_info
                        return
                elif field == "descricao":
                    expense["descricao"] = message.text.strip()
                elif field == "data":
                    expense["data_gasto"] = message.text.strip()
                try:
                    com_comprovante = bool(state.get("telegram_file_id"))
                    bot.edit_message_text(
                        _preview_text(expense, com_comprovante),
                        chat_id, confirm_msg_id,
                        reply_markup=_keyboard_confirm(),
                    )
                except Exception:
                    pass
            return

        if message.text == "💸":
            _start_gastos_flow(message, user_id, None)
            return
        if message.text == "📎":
            _start_comp_flow(message, user_id, None)
            return
        if message.text == "❓":
            handle_help(message)
            return
        if message.text == "🧹":
            ids = _chat_bot_msgs.pop(chat_id, [])
            for mid in ids:
                try:
                    bot.delete_message(chat_id, mid)
                except Exception:
                    pass
            return

        today = datetime.now().strftime("%Y-%m-%d")
        resultado = _classify(message.text, today)
        if resultado is None:
            sent = bot.reply_to(message, "❌ Não consegui entender. Tente novamente ou use /help.", reply_markup=_reply_keyboard())
            _track_msg(chat_id, sent.message_id)
            return
        intent = resultado.get("intent")

        if intent == "registrar":
            if not resultado.get("valido", False):
                sent = bot.reply_to(message, "ℹ️ Manda um gasto pra eu registrar! Ex: 'Almoço 35 reais' ou 'Netflix 45,90'.", reply_markup=_reply_keyboard())
                _track_msg(chat_id, sent.message_id)
                return
            expense = {
                "valor": resultado.get("valor", 0),
                "categoria": resultado.get("categoria", "Outros"),
                "descricao": resultado.get("descricao", ""),
                "data_gasto": resultado.get("data_gasto", today),
            }
            sent = bot.reply_to(message, _preview_text(expense), reply_markup=_keyboard_confirm())
            _track_msg(chat_id, sent.message_id)
            _pending_expense[(message.chat.id, sent.message_id)] = {
                "expense": expense,
                "requesting_user_id": user_id,
                "username": message.from_user.username or "",
                "mensagem_original": message.text,
                "telegram_file_id": None,
            }

        elif intent == "gastos":
            _start_gastos_flow(message, user_id, resultado.get("periodo"))

        elif intent == "comprovantes":
            _start_comp_flow(message, user_id, resultado.get("mes"))

        elif intent == "ajuda":
            handle_help(message)

        else:
            sent = bot.reply_to(message, "ℹ️ Não entendi. Use /help para ver o que posso fazer.", reply_markup=_reply_keyboard())
            _track_msg(chat_id, sent.message_id)

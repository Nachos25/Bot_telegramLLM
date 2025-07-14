import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from llm import generate_reply
from calendar_api import list_free_slots, create_appointment
from config import TELEGRAM_TOKEN
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

# Зберігаємо історію діалогу для кожного користувача
user_histories = {}

# FAQ для prompt (можна розширювати)
FAQ = (
    "Q: З якого віку можна робити лазерну епіляцію?\n"
    "A: Зазвичай з 18 років, але іноді з 16 за згодою батьків.\n"
    "Q: Це боляче?\n"
    "A: Сучасне обладнання робить процедуру максимально комфортною.\n"
    "Q: Чому це дорого?\n"
    "A: Це інвестиція у ваш комфорт і здоров'я, результат тримається довго."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вітаю! Я — AI-менеджер клініки лазерної епіляції. Чим можу допомогти?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    history = user_histories.get(user_id, [])
    # Додаємо повідомлення користувача в історію
    history.append({"role": "user", "content": text})
    # Додаємо FAQ на початок історії для контексту
    messages = [{"role": "system", "content": FAQ}] + history[-10:]
    reply = generate_reply(messages)
    # Додаємо відповідь бота в історію
    history.append({"role": "assistant", "content": reply})
    user_histories[user_id] = history[-20:]
    await update.message.reply_text(reply)
    # Якщо користувач хоче записатися — пропонуємо слоти
    if any(
        word in text.lower()
        for word in ["записатися", "записатись", "хочу на процедуру", "можна записатися"]
    ):
        await suggest_slots(update, context)


async def suggest_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    end = now + timedelta(days=7)
    slots = list_free_slots(
        start_iso=now.isoformat(),
        end_iso=end.isoformat(),
        duration_minutes=30
    )
    if not slots:
        await update.message.reply_text(
            "Вибачте, немає вільних слотів на найближчий тиждень."
        )
        return
    slot_texts = [
        f"{s[0].strftime('%d.%m %H:%M')} - "
        f"{s[1].strftime('%H:%M')}" for s in slots[:5]
    ]
    keyboard = [[s] for s in slot_texts]
    await update.message.reply_text(
        "Оберіть зручний час:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    context.user_data['pending_slots'] = slots[:5]
    context.user_data['awaiting_slot'] = True


async def handle_slot_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_slot'):
        return
    text = update.message.text
    slots = context.user_data.get('pending_slots', [])
    for slot in slots:
        slot_str = (
            f"{slot[0].strftime('%d.%m %H:%M')} - "
            f"{slot[1].strftime('%H:%M')}"
        )
        if text == slot_str:
            # Створюємо запис
            create_appointment(
                specialist="laserepilation",
                start_iso=slot[0].isoformat(),
                end_iso=slot[1].isoformat(),
                summary="Лазерна епіляція",
                description=f"Клієнт: {update.message.from_user.full_name}"
            )
            await update.message.reply_text(
                f"Запис підтверджено ✅ Чекаємо вас "
                f"{slot[0].strftime('%d.%m о %H:%M')}"
            )
            context.user_data['awaiting_slot'] = False
            return
    await update.message.reply_text(
        "Будь ласка, оберіть час із запропонованих варіантів."
    )


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    )
    app.add_handler(MessageHandler(filters.TEXT, handle_slot_selection))
    app.run_polling()


if __name__ == "__main__":
    main() 
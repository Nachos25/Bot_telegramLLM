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

# Храним историю диалога для каждого пользователя
user_histories = {}

# Пример FAQ для prompt (можно расширять)
FAQ = (
    "Q: С какого возраста можно делать лазерную эпиляцию?\n"
    "A: Обычно с 18 лет, но иногда с 16 с разрешения родителей.\n"
    "Q: Это больно?\n"
    "A: Современные аппараты делают процедуру максимально комфортной.\n"
    "Q: Почему так дорого?\n"
    "A: Это инвестиция в ваше удобство и здоровье, результат держится долго."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте! Я — AI-менеджер клиники лазерной эпиляции. "
        "Чем могу помочь?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    history = user_histories.get(user_id, [])
    # Добавляем сообщение пользователя в историю
    history.append({"role": "user", "content": text})
    # Добавляем FAQ в начало истории для контекста
    messages = [{"role": "system", "content": FAQ}] + history[-10:]
    reply = generate_reply(messages)
    # Добавляем ответ бота в историю
    history.append({"role": "assistant", "content": reply})
    user_histories[user_id] = history[-20:]
    await update.message.reply_text(reply)
    # Если пользователь хочет записаться, предлагаем слоты
    if any(
        word in text.lower()
        for word in ["записаться", "хочу на процедуру", "можно записаться"]
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
            "Извините, нет свободных слотов на ближайшую неделю."
        )
        return
    slot_texts = [
        f"{s[0].strftime('%d.%m %H:%M')} - "
        f"{s[1].strftime('%H:%M')}" for s in slots[:5]
    ]
    keyboard = [[s] for s in slot_texts]
    await update.message.reply_text(
        "Выберите удобное время:",
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
            # Создаем запись
            create_appointment(
                specialist="laserepilation",
                start_iso=slot[0].isoformat(),
                end_iso=slot[1].isoformat(),
                summary="Лазерная эпиляция",
                description=f"Клиент: {update.message.from_user.full_name}"
            )
            await update.message.reply_text(
                f"Запись подтверждена ✅ Чекаємо вас "
                f"{slot[0].strftime('%d.%m о %H:%M')}"
            )
            context.user_data['awaiting_slot'] = False
            return
    await update.message.reply_text(
        "Пожалуйста, выберите время из "
        "предложенных вариантов."
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
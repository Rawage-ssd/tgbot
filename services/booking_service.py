import sqlite3
from telebot import TeleBot, types
from bot.keyboards.inline import get_workout_types_keyboard

DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
TIMES = [f"{hour:02d}:00" for hour in range(9, 19)]


def init_db():
    conn = sqlite3.connect("gym_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            workout_type TEXT,
            day TEXT,
            time TEXT
        )
    """)
    conn.commit()
    conn.close()


def safe_answer_callback(bot: TeleBot, call_id: str, text: str = None):
    try:
        bot.answer_callback_query(call_id, text=text)
    except Exception:
        pass


def get_days_keyboard(workout_type: str) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    buttons = [
        types.InlineKeyboardButton(
            text=day, callback_data=f"day|{workout_type}|{day}"
        )
        for day in DAYS
    ]
    keyboard.add(*buttons)
    return keyboard


# ГЕНЕРАТОР КНОПОК ВРЕМЕНИ С ПРОВЕРКОЙ ЗАНЯТОСТИ (1 человек на слот)
def get_times_keyboard(
    workout_type: str, day: str
) -> types.InlineKeyboardMarkup:
    conn = sqlite3.connect("gym_bot.db")
    cursor = conn.cursor()
    # Получаем все уже занятые слоты на этот день для данного направления
    cursor.execute(
        "SELECT time FROM bookings WHERE workout_type = ? AND day = ?",
        (workout_type, day),
    )
    booked_times = [row[0] for row in cursor.fetchall()]
    conn.close()

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = []

    for t in TIMES:
        if t in booked_times:
            # Занятое время: кнопка неактивна (callback_data="occupied")
            buttons.append(
                types.InlineKeyboardButton(
                    text=f"❌ {t} (Занято)", callback_data="occupied"
                )
            )
        else:
            # Свободное время
            buttons.append(
                types.InlineKeyboardButton(
                    text=f"🟢 {t}", callback_data=f"time|{workout_type}|{day}|{t}"
                )
            )

    keyboard.add(*buttons)
    return keyboard


# Главная клавиатура с кнопкой перезапуска
def get_main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_book = types.KeyboardButton("🏋️ Записаться")
    btn_my_bookings = types.KeyboardButton("📅 Мои записи")
    btn_help = types.KeyboardButton("ℹ️ Помощь")
    btn_restart = types.KeyboardButton("🔄 Перезапуск")

    keyboard.add(btn_book, btn_my_bookings, btn_help, btn_restart)
    return keyboard


def register_booking_handlers(bot: TeleBot):
    init_db()

    # Обработка /start и кнопки "🔄 Перезапуск"
    @bot.message_handler(
        commands=["start"], func=lambda msg: True if not msg.text else False
    )
    @bot.message_handler(
        func=lambda msg: msg.text in ["/start", "🔄 Перезапуск"]
    )
    def send_welcome(message: types.Message):
        bot.send_message(
            message.chat.id,
            f"Бот перезапущен! 👋\n\nВыберите нужный раздел из меню ниже:",
            reply_markup=get_main_menu_keyboard(),
        )

    # 1. Нажатие кнопки "🏋️ Записаться"
    @bot.message_handler(func=lambda msg: msg.text == "🏋️ Записаться")
    def start_booking(message: types.Message):
        bot.send_message(
            message.chat.id,
            "Выберите направление обучения:",
            reply_markup=get_workout_types_keyboard(),
        )

    # 2. Мои записи
    @bot.message_handler(func=lambda msg: msg.text == "📅 Мои записи")
    def show_my_bookings(message: types.Message):
        conn = sqlite3.connect("gym_bot.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT workout_type, day, time FROM bookings WHERE user_id = ?",
            (message.from_user.id,),
        )
        user_bookings = cursor.fetchall()
        conn.close()

        if not user_bookings:
            bot.send_message(
                message.chat.id, "У вас пока нет активных записей."
            )
            return

        response = "📋 <b>Ваши записи:</b>\n\n"
        for item in user_bookings:
            response += f"🔹 <b>{item[0]}</b> — {item[1]} в {item[2]}\n"

        bot.send_message(message.chat.id, response, parse_mode="HTML")

    # 3. Выбор направления
    @bot.callback_query_handler(func=lambda call: call.data.startswith("type_"))
    def handle_workout_selection(call: types.CallbackQuery):
        safe_answer_callback(bot, call.id)

        topics = {
            "type_web": "🌐 Веб-разработка",
            "type_ai": "🤖 ИИ и Machine Learning",
            "type_mobile": "📱 Мобильная разработка",
            "type_python": "🐍 Python Разработка",
        }
        selected = topics.get(call.data, "Курс/Воркшоп")

        bot.edit_message_text(
            f"Вы выбрали: <b>{selected}</b>\n\n📅 Выберите день недели:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_days_keyboard(call.data),
        )

    # 4. Выбор дня
    @bot.callback_query_handler(func=lambda call: call.data.startswith("day|"))
    def handle_day_selection(call: types.CallbackQuery):
        safe_answer_callback(bot, call.id)

        _, workout_type, selected_day = call.data.split("|")

        bot.edit_message_text(
            f"📅 Выбранный день: <b>{selected_day}</b>\n\n⏰ Выберите свободное время:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_times_keyboard(workout_type, selected_day),
        )

    # 5. Клик по ЗАНЯТОЙ кнопке
    @bot.callback_query_handler(func=lambda call: call.data == "occupied")
    def handle_occupied_click(call: types.CallbackQuery):
        safe_answer_callback(
            bot,
            call.id,
            text="❌ Это время уже занято! Выберите другое слот.",
        )

    # 6. Выбор времени -> Защита от race condition и сохранение
    @bot.callback_query_handler(func=lambda call: call.data.startswith("time|"))
    def handle_time_selection(call: types.CallbackQuery):
        _, workout_type, selected_day, selected_time = call.data.split("|")

        topics = {
            "type_web": "🌐 Веб-разработка",
            "type_ai": "🤖 ИИ и Machine Learning",
            "type_mobile": "📱 Мобильная разработка",
            "type_python": "🐍 Python Разработка",
        }
        workout_name = topics.get(workout_type, "Занятие")

        conn = sqlite3.connect("gym_bot.db")
        cursor = conn.cursor()

        # Повторная проверка прямо перед записью
        cursor.execute(
            "SELECT id FROM bookings WHERE workout_type = ? AND day = ? AND time = ?",
            (workout_name, selected_day, selected_time),
        )
        if cursor.fetchone():
            conn.close()
            safe_answer_callback(
                bot, call.id, text="Упс! Кто-то только что занял это время."
            )
            return

        cursor.execute(
            "INSERT INTO bookings (user_id, username, workout_type, day, time) VALUES (?, ?, ?, ?, ?)",
            (
                call.from_user.id,
                call.from_user.username or call.from_user.first_name,
                workout_name,
                selected_day,
                selected_time,
            ),
        )
        conn.commit()
        conn.close()

        safe_answer_callback(bot, call.id)

        bot.edit_message_text(
            f"✅ <b>Запись успешно сохранена!</b>\n\n"
            f"🔹 Направление: {workout_name}\n"
            f"📅 День: {selected_day}\n"
            f"⏰ Время: {selected_time}\n\n"
            f"Место забронировано за вами.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
        )
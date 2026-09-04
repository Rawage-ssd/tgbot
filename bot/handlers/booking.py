import sqlite3
from telebot import TeleBot, types
from bot.keyboards.inline import get_workout_types_keyboard

# Дни недели и слоты времени с 09:00 до 18:00
DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
TIMES = [f"{hour:02d}:00" for hour in range(9, 19)]


# Инициализация базы данных
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


# Безопасный ответ на callback
def safe_answer_callback(bot: TeleBot, call_id: str):
    try:
        bot.answer_callback_query(call_id)
    except Exception:
        pass


# --- Генераторы Inline-клавиатур ---
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


def get_times_keyboard(
    workout_type: str, day: str
) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    buttons = [
        types.InlineKeyboardButton(
            text=t, callback_data=f"time|{workout_type}|{day}|{t}"
        )
        for t in TIMES
    ]
    keyboard.add(*buttons)
    return keyboard


# Главное меню с 4 кнопками
def get_main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_book = types.KeyboardButton("🏋️ Записаться")
    btn_my_bookings = types.KeyboardButton("📅 Мои записи")
    btn_help = types.KeyboardButton("ℹ️ Помощь")
    btn_profile = types.KeyboardButton("👤 Профиль")

    keyboard.add(btn_book, btn_my_bookings, btn_help, btn_profile)
    return keyboard


# --- Регистрация хэндлеров ---
def register_booking_handlers(bot: TeleBot):
    init_db()

    # 1. Команда /start
    @bot.message_handler(commands=["start"])
    def send_welcome(message: types.Message):
        bot.send_message(
            message.chat.id,
            f"Привет, {message.from_user.first_name}! 👋\n\n"
            f"Выберите нужный раздел из меню ниже:",
            reply_markup=get_main_menu_keyboard(),
        )

    # 2. Кнопка "🏋️ Записаться"
    @bot.message_handler(func=lambda msg: msg.text == "🏋️ Записаться")
    def start_booking(message: types.Message):
        bot.send_message(
            message.chat.id,
            "Выберите направление обучения:",
            reply_markup=get_workout_types_keyboard(),
        )

    # 3. Кнопка "📅 Мои записи"
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

    # 4. Кнопка "👤 Профиль"
    @bot.message_handler(func=lambda msg: msg.text == "👤 Профиль")
    def show_profile(message: types.Message):
        user = message.from_user
        username = f"@{user.username}" if user.username else "Не указан"

        profile_text = (
            f"👤 <b>Ваш профиль:</b>\n\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"👤 <b>Имя:</b> {user.first_name}\n"
            f"🔗 <b>Username:</b> {username}"
        )
        bot.send_message(message.chat.id, profile_text, parse_mode="HTML")

    # 5. Кнопка "ℹ️ Помощь"
    @bot.message_handler(func=lambda msg: msg.text == "ℹ️ Помощь")
    def show_help(message: types.Message):
        help_text = (
            "ℹ️ <b>Справка по боту:</b>\n\n"
            "• <b>Записаться</b> — выбрать направление, день недели и время.\n"
            "• <b>Мои записи</b> — просмотреть список ваших тренировок.\n"
            "• <b>Профиль</b> — ваши данные в системах Telegram."
        )
        bot.send_message(message.chat.id, help_text, parse_mode="HTML")

    # --- Обработка кликов по инлайн-кнопкам ---

    # Выбор направления -> Вывод ДНЕЙ
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

    # Выбор дня -> Вывод ВРЕМЕНИ
    @bot.callback_query_handler(func=lambda call: call.data.startswith("day|"))
    def handle_day_selection(call: types.CallbackQuery):
        safe_answer_callback(bot, call.id)

        _, workout_type, selected_day = call.data.split("|")

        bot.edit_message_text(
            f"📅 Выбранный день: <b>{selected_day}</b>\n\n⏰ Выберите время (09:00 - 18:00):",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_times_keyboard(workout_type, selected_day),
        )

    # Выбор времени -> Сохранение в БД и Финал
    @bot.callback_query_handler(func=lambda call: call.data.startswith("time|"))
    def handle_time_selection(call: types.CallbackQuery):
        safe_answer_callback(bot, call.id)

        _, workout_type, selected_day, selected_time = call.data.split("|")

        topics = {
            "type_web": "🌐 Веб-разработка",
            "type_ai": "🤖 ИИ и Machine Learning",
            "type_mobile": "📱 Мобильная разработка",
            "type_python": "🐍 Python Разработка",
        }
        workout_name = topics.get(workout_type, "Занятие")

        # Сохранение записи в базу
        conn = sqlite3.connect("gym_bot.db")
        cursor = conn.cursor()
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

        bot.edit_message_text(
            f"✅ <b>Запись успешно сохранена!</b>\n\n"
            f"🔹 Направление: {workout_name}\n"
            f"📅 День: {selected_day}\n"
            f"⏰ Время: {selected_time}\n\n"
            f"Ждем вас на занятии!",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
        )
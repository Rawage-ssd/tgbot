from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_workout_types_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    
    btn1 = InlineKeyboardButton("🌐 Веб-разработка", callback_data="type_web")
    btn2 = InlineKeyboardButton("🤖 ИИ и Machine Learning", callback_data="type_ai")
    btn3 = InlineKeyboardButton("📱 Мобильная разработка", callback_data="type_mobile")
    btn4 = InlineKeyboardButton("🐍 Python Разработка", callback_data="type_python")
    
    markup.add(btn1, btn2, btn3, btn4)
    return markup
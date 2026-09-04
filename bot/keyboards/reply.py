from telebot import types

def get_main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn_book = types.KeyboardButton("🏋️ Записаться")
    btn_my_bookings = types.KeyboardButton("📅 Мои записи")
    btn_profile = types.KeyboardButton("👤 Профиль")
    btn_help = types.KeyboardButton("ℹ️ Помощь")
    
    markup.add(btn_book, btn_my_bookings)
    markup.add(btn_profile, btn_help)
    return markup
from telebot import TeleBot, types
from bot.keyboards.reply import get_main_menu_keyboard

def register_start_handlers(bot: TeleBot):
    
    @bot.message_handler(commands=['start'])
    def send_welcome(message: types.Message):
        text = (
            f"Привет, <b>{message.from_user.first_name}</b>! 👋\n\n"
            "Добро пожаловать в фитнес-клуб.\n"
            "Воспользуйтесь меню ниже для записи на занятие."
        )
        bot.send_message(
            message.chat.id, 
            text, 
            reply_markup=get_main_menu_keyboard(), 
            parse_mode="HTML"
        )

    @bot.message_handler(func=lambda msg: msg.text == "ℹ️ Помощь")
    def send_help(message: types.Message):
        text = (
            "<b>ℹ️ Справка</b>\n\n"
            "• <b>Записаться:</b> Выбор направления, даты и времени.\n"
            "• <b>Мои записи:</b> Просмотр активных броней и их отмена.\n"
            "• <b>Профиль:</b> Ваши личные данные.\n\n"
            "По вопросам работы бота обращаться к администратору."
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    @bot.message_handler(func=lambda msg: msg.text == "📅 Мои записи")
    def show_my_bookings(message: types.Message):
        bot.send_message(message.chat.id, "📅 У вас пока нет активных записей.", parse_mode="HTML")

    @bot.message_handler(func=lambda msg: msg.text == "👤 Профиль")
    def show_profile(message: types.Message):
        bot.send_message(
            message.chat.id, 
            f"👤 <b>Ваш профиль:</b>\nИмя: {message.from_user.first_name}\nID: {message.from_user.id}", 
            parse_mode="HTML"
        )
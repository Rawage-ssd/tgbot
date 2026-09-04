from telebot import TeleBot
from bot.handlers.booking import register_booking_handlers

# Считываем токен из файла
with open("token.txt", "r", encoding="utf-8") as f:
    BOT_TOKEN = f.read().strip()

bot = TeleBot(BOT_TOKEN)

# Регистрируем все кнопки и хэндлеры
register_booking_handlers(bot)

if __name__ == "__main__":
    print("🤖 Бот запущен и ожидает сообщений...")
    bot.infinity_polling(skip_pending=True)
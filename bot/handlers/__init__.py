from telebot import TeleBot
from bot.handlers.start import register_start_handlers
from bot.handlers.booking import register_booking_handlers


def register_all_handlers(bot: TeleBot):
    register_start_handlers(bot)
    register_booking_handlers(bot)
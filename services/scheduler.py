from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from db.base import SessionLocal
from db.models import Booking, Schedule

# Вспомогательный сет для исключения дубликатов отправки
sent_reminders = set()

def check_and_send_reminders(bot):
    db = SessionLocal()
    try:
        now = datetime.now()
        
        # Получаем все активные бронирования с будущими занятиями
        active_bookings = db.scalars(
            select(Booking)
            .options(joinedload(Booking.schedule).joinedload(Schedule.category), joinedload(Booking.user))
            .where(
                Booking.status == "active",
                Booking.schedule.has(Schedule.start_time > now)
            )
        ).all()

        for booking in active_bookings:
            start_time = booking.schedule.start_time
            time_diff = start_time - now
            
            # Напоминание за 24 часа (окно в 15 минут)
            rem_24_key = f"24h_{booking.id}"
            if timedelta(hours=23, minutes=45) <= time_diff <= timedelta(hours=24, minutes=15):
                if rem_24_key not in sent_reminders:
                    bot.send_message(
                        booking.user.telegram_id,
                        f"⏰ <b>Напоминание!</b>\n\nЗавтра в {start_time.strftime('%H:%M')} у вас занятие по <b>{booking.schedule.category.title}</b>!",
                        parse_mode="HTML"
                    )
                    sent_reminders.add(rem_24_key)

            # Напоминание за 2 часа (окно в 15 минут)
            rem_2h_key = f"2h_{booking.id}"
            if timedelta(hours=1, minutes=45) <= time_diff <= timedelta(hours=2, minutes=15):
                if rem_2h_key not in sent_reminders:
                    bot.send_message(
                        booking.user.telegram_id,
                        f"🚨 <b>Скоро занятие!</b>\n\nЧерез 2 часа ({start_time.strftime('%H:%M')}) состоится занятие по <b>{booking.schedule.category.title}</b> в {booking.schedule.room or 'зале'}!",
                        parse_mode="HTML"
                    )
                    sent_reminders.add(rem_2h_key)
    except Exception as e:
        print(f"Ошибка в планировщике напоминаний: {e}")
    finally:
        db.close()

def start_scheduler(bot):
    scheduler = BackgroundScheduler()
    # Проверка каждые 15 минут
    scheduler.add_job(check_and_send_reminders, 'interval', minutes=15, args=[bot])
    scheduler.start()
    print("⏰ Планировщик фоновых задач APScheduler запущен.")
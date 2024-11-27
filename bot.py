import logging
import asyncio
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from handlers.start import router, setup_scheduler
from settings.settings import settings
from database.models import session, Event, User

scheduler = AsyncIOScheduler()

async def send_reminders(bot: Bot):
    now = datetime.now()
    tomorrow = now + timedelta(days=1)

    events = session.query(Event).filter(
        Event.notification_time.between(now, tomorrow)
    ).all()

    for event in events:
        user = session.query(User).filter_by(id=event.user_id).first()
        if user:
            try:
                await bot.send_message(
                    user.telegram_id,
                    f"Напоминание: {event.event_name} запланировано на {event.event_date.strftime('%Y-%m-%d %H:%M')}!"
                )
            except Exception as e:
                logging.error(f"Не удалось отправить сообщение {user.telegram_id}: {e}")

async def main():

    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.bots.token_bot)
    dp = Dispatcher()

    dp.include_router(router)

    scheduler.add_job(
        send_reminders,
        "cron",
        hour=9,
        kwargs={"bot": bot}
    )
    setup_scheduler(scheduler)

    scheduler.start()
    logging.info("Планировщик запущен")

    try:
        logging.info("Бот запущен")
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logging.exception(f"Произошла ошибка: {e}")
    finally:
        await bot.session.close()
        scheduler.shutdown(wait=False)

if __name__ == "__main__":
    asyncio.run(main())

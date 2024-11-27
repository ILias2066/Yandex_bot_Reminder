import requests
import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from ics import Calendar
from datetime import timedelta
from database.models import session, User, Event

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Отправь мне ссылку на экспорт Яндекс.Календаря в формате `.ics`. "
        "Например, 'https://calendar.yandex.ru/export/ics.xml?...'"
    )

@router.message(lambda msg: "export/ics.xml" in msg.text)
async def sync_calendar(message: Message):
    calendar_url = message.text.strip()
    user_id = message.from_user.id

    user = session.query(User).filter_by(telegram_id=user_id).first()
    if not user:
        user = User(telegram_id=user_id, calendar_url=calendar_url)
        session.add(user)
        session.commit()
    else:
        user.calendar_url = calendar_url
        session.commit()

    try:
        response = requests.get(calendar_url)

        if response.status_code != 200:
            raise Exception(f"Не удалось загрузить календарь. Статус: {response.status_code}")

        calendar = Calendar(response.text)

        events = []
        for event in calendar.events:
            events.append({
                "summary": event.name,
                "start": event.begin.datetime,
                "end": event.end.datetime,
            })

        save_events_to_db(user.id, events)

        await message.answer("Календарь успешно синхронизирован! Напоминания будут отправлены за день до события.")
    except Exception as e:
        await message.answer(f"Произошла ошибка при синхронизации: {e}")


def save_events_to_db(user_id, events):
    for event in events:
        event_date = event["start"]
        event_name = event["summary"]
        notification_time = event_date - timedelta(days=1)

        existing_event = session.query(Event).filter_by(
            user_id=user_id,
            event_name=event_name,
            event_date=event_date
        ).first()

        if not existing_event:
            event_record = Event(
                user_id=user_id,
                event_name=event_name,
                event_date=event_date,
                notification_time=notification_time
            )
            session.add(event_record)

    session.commit()


def update_calendar():
    users = session.query(User).all()
    for user in users:
        if not user.calendar_url:
            continue

        try:
            response = requests.get(user.calendar_url)
            if response.status_code != 200:
                print(f"Не удалось загрузить календарь для пользователя {user.id}. Статус: {response.status_code}")
                continue

            calendar = Calendar(response.text)
            events = []
            for event in calendar.events:
                events.append({
                    "summary": event.name,
                    "start": event.begin.datetime,
                    "end": event.end.datetime,
                })

            save_events_to_db(user.id, events)
            print(f"Календарь пользователя {user.id} успешно обновлён.")
        except Exception as e:
            print(f"Ошибка при обновлении календаря для пользователя {user.id}: {e}")


def setup_scheduler(scheduler):
    scheduler.add_job(
        update_calendar,
        trigger="interval",
        hours=5,
        id="update_calendar_job",
        replace_existing=True,
    )
    logging.info("Планировщик настроен: обновление календаря каждые 5 часов.")

# /////////////
# Time reminder
# /////////////

from app.keyboards import markup
from aiogram.types import Message
from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.keyboards import main
from apscheduler.triggers.date import DateTrigger
from zoneinfo import ZoneInfo

import datetime as dt
import logging
import os

reminderr = Router()
scheduler = AsyncIOScheduler(timezone="UTC")

logger = logging.getLogger(__name__)

# Пользователь вводит время по своим часам, а планировщик работает в UTC.
# Без явного часового пояса напоминание "на 10:00" срабатывало в 13:00 по Москве.
USER_TZ = ZoneInfo(os.getenv("BOT_TIMEZONE", "Europe/Moscow"))


class Add_reminder(StatesGroup):
    new_rem = State()
    
async def send_reminder(bot: Bot, chat_id: int, state: FSMContext):
    try:
        await bot.send_message(chat_id, 'Напоминаю!', reply_markup=main)
        logger.info(
            "Напоминание отправлено для %s",
            chat_id
            )
        await state.clear()
        # await shutdown_scheduler()
    except Exception as e:
        logger.error(
            "Ошибка отправки напоминания для %s: %s",
            chat_id,e
            )
        
async def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("Планировщик запущен")

# async def shutdown_scheduler():
#     if scheduler.running:
#         scheduler.shutdown()
#         logger.info("Планировщик остановлен")

@reminderr.message(F.text == 'Установить напоминание')
async def remind(message: Message, state: FSMContext):
    await state.set_state(Add_reminder.new_rem)
    await message.answer('Напишите в какое время Вам напоминить?\nВ формате ДД.ММ ЧЧ:ММ', reply_markup=markup)

@reminderr.message(Add_reminder.new_rem)
async def add_rem(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(new_rem=message.text)
    
    try:
        now = dt.datetime.now(USER_TZ)
        # Год добавляем ДО разбора: без года strptime не понимает 29.02
        # (и в Python 3.15 такой разбор станет ошибкой).
        time_from_user = dt.datetime.strptime(f"{message.text.strip()} {now.year}", '%d.%m %H:%M %Y')
        logger.info("%s успешно преобразовано",
                    time_from_user
                    )
        
        time_from_user = time_from_user.replace(tzinfo=USER_TZ)
        if time_from_user <= now:
            await message.answer('Это время уже прошло. Укажите время в будущем: ДД.ММ ЧЧ:ММ')
            return
        
        await message.answer(
            f'Напоминание установлено на {time_from_user.strftime("%d.%m %H:%M")}', 
            reply_markup=main
        )
        logger.info("Напоминание установлено для %s на %s",
                    *[message.chat.id,time_from_user],
                    )
        
        await start_scheduler()
        scheduler.add_job(
            send_reminder,
            trigger=DateTrigger(run_date=time_from_user),
            args=[bot, message.chat.id, state],
            id=f"reminder_{message.chat.id}_{time_from_user.timestamp()}"
        )

    except ValueError:
        await message.answer('Неверный формат времени. Используйте ДД.ММ ЧЧ:ММ')
        logger.error("Неверный формат времени от пользователя")
    except Exception as e:
        logger.error("Ошибка при установке напоминания: %s",
                     e,
                     exc_info=True
                    )
        await message.answer('Произошла ошибка при установке напоминания')
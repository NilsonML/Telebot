# ////////////////
# Hanldlers for AI
# ////////////////

from app.generate import ai_generate
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router
from aiogram.types import Message
from aiogram import F
from app.handlers_user import cpfc
from aiogram.enums import ParseMode

import app.database.requests_for_users as rq
import logging

class Gen(StatesGroup):
    wait = State()

air = Router()

logger = logging.getLogger(__name__)

@air.message(Gen.wait)
async def stop_flood(message: Message):
    await message.answer("Подождите, Ваш запрос обрабатывается")


@air.message(F.text == 'Составить меню на день')
async def generating(message: Message, state: FSMContext):
    max_len = 4096
    cw = float(await rq.get_current_weight(message.from_user.id))
    dw = float(await rq.get_desired_weight(message.from_user.id))
    difr = dw - cw
    pref = str(*await rq.get_pref(message.from_user.id))
    dis = str(*await rq.get_dis(message.from_user.id))
    num = str(*await rq.get_num_of_meals(message.from_user.id))
    cost = str(*await rq.get_cost(message.from_user.id))
    try:
        if difr > 0:
            text_for_ii = f'''Составь меню на один день(только блюда без описаний)
    c учетом моих пожеланий: {pref}
    и моих болезней: {dis} и чтобы набрать {difr} кг, КБЖУ {await cpfc(message.from_user.id)}, {num} приемов пищи и с бюджетом {cost} руб'''
        elif difr < 0:
            text_for_ii = f'''Составь меню на один день(только блюда без описаний)
    c учетом моих пожеланий: {pref}
    и моих болезней: {dis} и чтобы сбросить {abs(difr)} кг, КБЖУ {await cpfc(message.from_user.id)}, {num} приемов пищи и с бюджетом {cost} руб'''
        else:
            text_for_ii = f'''Составь меню на один день(только блюда без описаний)
    c учетом моих пожеланий: {pref}
    и моих болезней: {dis} чтобы поддерживать вес {cw} кг, КБЖУ {await cpfc(message.from_user.id)}, {num} приемов пищи и с бюджетом {cost} руб'''
        
        logger.info(
            "Текст для ИИ успешно создан"
        )
    except Exception:
        # Без return дальше был бы NameError: text_for_ii не определён
        logger.exception("Текст для ИИ не создан")
        await message.answer("Не удалось составить запрос. Проверьте, что анкета заполнена.")
        return
    
    try:
        await state.set_state(Gen.wait)
        responce = await ai_generate(text_for_ii)
        for i in range(0, len(responce), max_len):
            part = responce[i:i + max_len]
            await message.answer(escape_markdown(part), parse_mode="MarkdownV2")
        logger.info(
            "Текст пользователю успешно отправлен"
        )
        await state.clear()
    except Exception as e:
        logger.error(
            "Текст не отправлен пользователю, ошибка: %s!!!", e)
        await state.clear()
        return
    
def escape_markdown(text: str) -> str:
    """Экранирует специальные символы MarkdownV2"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)
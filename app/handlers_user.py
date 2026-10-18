# ///////////////////
# Hanldlers for users
# ///////////////////

from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, or_f
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.keyboards import markup
from aiogram.types import Message

import app.keyboards as kb
import app.database.requests_for_users as rq
import logging

logger = logging.getLogger(__name__)

def is_valid_message(text):
    return (any(char.isalpha() for char in text) and len(text) >= 3) or text == "-"

coefficient = {1: 1.2, 2: 1.375, 3: 1.55, 4: 1.725, 5: 1.9}

async def cpfc(tg_id):    
    formula = int()
    cw = float(await rq.get_current_weight(tg_id))
    dw = float(await rq.get_desired_weight(tg_id))
    sex = str(await rq.get_sex(tg_id))
    age = int(await rq.get_age(tg_id))
    height = float(await rq.get_height(tg_id))
    physact = int(await rq.get_phys_act(tg_id))
    difr = dw - cw
    if difr == 0 and sex == 'м':
        formula = (10*cw) + (6.25*height) - (5*age) + 5
    if difr == 0 and sex == 'ж':
        formula = (10*cw) + (6.25*height) - (5*age) - 161
    if difr > 0 and sex == 'м':                             #если difr > 0, то прибавляем к текущему каллоражу 150 ккал
        formula = (10*cw) + (6.25*height) - (5*age) + 155 
    if difr > 0  and sex == 'ж':
        formula = (10*cw) + (6.25*height) - (5*age) - 11
    if difr < 0 and sex == 'м':                             #если difr < 0, то убавляем к текущему каллоражу 150 ккал
        formula = (10*cw) + (6.25*height) - (5*age) - 145
    if difr < 0 and sex == 'ж':
        formula = (10*cw) + (6.25*height) - (5*age) - 311

    calories = formula*coefficient[physact]
    proteins = cw*1.3
    fats = cw*1.1
    carbohydrates = cw*8
    logger.info(
            "КБЖУ для %s успешно вычислены",
            tg_id
            )
    return  f'''{int(calories)}/{int(proteins)}/{int(fats)}/{int(carbohydrates)}'''

userr = Router()

class Reg(StatesGroup):
    age = State()
    sex = State()
    physical_activity = State()
    diseases = State()
    preferences = State()
    current_weight = State()
    desired_weight = State()
    height = State()
    number_of_meals = State()
    cost = State()


class Add_new_pref(StatesGroup):
    new_pref = State()


class Add_new_dis(StatesGroup):
    new_dis = State()


@userr.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id)
    await message.answer((f'''Привет {message.from_user.first_name}!
я бот, который поможет составить тебе меню по нужным тебе КБЖУ с учетом предпочтений и проблем со здоровьем.
Для начала нужно зарегистрироваться'''),reply_markup=kb.reg)
    
@userr.message(or_f(F.text == 'Зарегистрироваться', F.text == 'Изменить данные'))
async def reg_age(message: Message, state: FSMContext):
    await state.set_state(Reg.age)
    await message.answer('Введите возраст',reply_markup=markup)

@userr.message(Reg.age)
async def reg_sex(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer('Пожалуйста, введите корректный возраст (число больше нуля)')
        return
    await state.update_data(age=message.text)
    await state.set_state(Reg.sex)
    await message.answer('Введите пол (м/ж)')

@userr.message(Reg.sex)
async def reg_lifestyle(message: Message, state: FSMContext):
    if message.text.lower() not in ['м', 'ж']:
        await message.answer('Пожалуйста, введите корректный пол (м/ж)')
        return
    await state.update_data(sex=message.text.lower())
    await message.answer('''Коэффициенты физической активности:
1. Сидячий образ жизни
2. Легкая активность (тренировки 1-3 раза в неделю)
3. Умеренная активность (тренировки 3-5 раз в неделю)
4. Высокая активность (тренировки 6-7 раз в неделю)
5. Очень высокая активность (тяжелые тренировки каждый день или 2 раза в день)
''')
    await state.set_state(Reg.physical_activity)
    await message.answer('Выберите физическую активность')

@userr.message(Reg.physical_activity)
async def reg_diseases(message: Message, state: FSMContext):
    if message.text not in ["1","2","3","4","5"]:
        await message.answer('Пожалуйста, введите цифру без точки')
        return
    await state.update_data(physical_activity=message.text)
    await state.set_state(Reg.diseases)
    await message.answer('Введите проблемы со здоровьем (если отсутствуют поставьте -)')

@userr.message(Reg.diseases)
async def reg_preferences(message: Message, state: FSMContext):
    if not is_valid_message(message.text):
        await message.answer('Пожалуйста, введите проблемы со здоровьем')
        return  
    await state.update_data(diseases=message.text)
    await state.set_state(Reg.preferences)
    await message.answer('Введите вкусовые предпочтения (если отсутствуют поставьте -)')

@userr.message(Reg.preferences)
async def reg_current_weight(message: Message, state: FSMContext):
    if not is_valid_message(message.text):
        await message.answer('Пожалуйста, введите предпочтения')
        return
    await state.update_data(preferences=message.text)
    await state.set_state(Reg.number_of_meals)
    await message.answer('Введите сколько приемов пищи в день')

@userr.message(Reg.number_of_meals)
async def reg_number_of_meals(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 0:
        await message.answer('Пожалуйста, введите количество приемов пищи в день')
        return
    await state.update_data(number_of_meals=message.text)
    await state.set_state(Reg.cost)
    await message.answer('Введите бюджет продуктов на неделю')

@userr.message(Reg.cost)
async def reg_cost(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer('Пожалуйста, введите бюджет на продукты')
        return
    await state.update_data(cost=message.text)
    await state.set_state(Reg.current_weight)
    await message.answer('Введите текущий вес')

@userr.message(Reg.current_weight)
async def reg_current_weight(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer('Пожалуйста, введите корректный текущий вес')
        return
    await state.update_data(current_weight=message.text)
    await state.set_state(Reg.desired_weight)
    await message.answer('Введите желаемый вес')

@userr.message(Reg.desired_weight)
async def reg_desired_weight(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer('Пожалуйста, введите корректный желаемый вес')
        return
    await state.update_data(desired_weight=message.text)
    await state.set_state(Reg.height)
    await message.answer('Введите рост')

@userr.message(Reg.height)
async def reg_height(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 120 or int(message.text) > 220:
        await message.answer('Пожалуйста, введите корректный рост')
        return
    await state.update_data(height=message.text)
    data = await state.get_data()
    await rq.add_info_user(data, message.from_user.id)
    info = await rq.get_info_user(message.from_user.id)
    for user in info:
        await message.answer(f'''Age: {user.age}
Sex: {user.sex}
Physical Activity: {user.physical_activity}
Diseases: {user.diseases}
Preferences: {user.preferences}
Current Weight: {user.current_weight}
Desired Weight: {user.desired_weight}
Height: {user.height}
Number of meals: {user.number_of_meals}
Cost: {user.cost}
КБЖУ - {await cpfc(message.from_user.id)}
    ''', reply_markup=kb.main)
    await state.clear()

@userr.message(F.text == 'Добавить проблему/предпочтение')
async def add_new(message: Message):
    await message.answer("Выберите что добавить", reply_markup=kb.add_new_pref_dis)

@userr.message(F.text == 'Предпочтение')
async def add_new_pref(message: Message, state: FSMContext):
    logger.info(
        "Команда успешно выполнена"
    )
    await state.set_state(Add_new_pref.new_pref)
    await message.answer('Добавлять по одному предпочтению за раз', reply_markup=markup)

@userr.message(Add_new_pref.new_pref)
async def add_new_pref(message: Message, state: FSMContext):
    await state.update_data(new_pref=message.text)
    new_pref = message.text
    pref = await rq.add_new_pref(new_pref, message.from_user.id)
    await message.answer(f"{pref}", reply_markup=kb.main)
    logger.info(
        "Предпочтения успешно добавлены"
    )
    await state.clear()

@userr.message(F.text == 'Проблему')
async def add_new_dis(message: Message, state: FSMContext):
    logger.info(
        "Команда успешно выполнена"
    )
    await state.set_state(Add_new_dis.new_dis)
    await message.answer('Добавлять по одной проблеме за раз', reply_markup=markup)

@userr.message(Add_new_dis.new_dis)
async def add_new_dis(message: Message, state: FSMContext):
    await state.update_data(new_dis=message.text)
    new_dis = message.text
    dis = await rq.add_new_dis(new_dis, message.from_user.id)
    logger.info(
        "Проблемы успешно добавлены"
    )
    await message.answer(f"{dis}", reply_markup=kb.main)
    await state.clear()

# @userr.message()
# async def not_but(message: Message):
#     print(dir(message))
#     print(message.from_user)
#     await message.answer('Выберите кнопку')
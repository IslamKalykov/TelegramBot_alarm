from aiogram.utils import executor
from aiogram import Bot, types
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from datetime import datetime
from dotenv import load_dotenv
from models import new_bot_users, insert_event, get_events, get_event_by_id, update_event, perform_delete_event, get_event_for_tomorrow, get_event_for_week, get_event_for_today

import os
import logging
import asyncio

load_dotenv()
# Замените 'YOUR_BOT_TOKEN' на токен, полученный от BotFather
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Инициализируем бота и диспетчер
storage = MemoryStorage()

bot = Bot(token=BOT_TOKEN)
# dp = Dispatcher(bot)
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    new_bot_users(user_id=user_id, user_name=username,
                  first_name=first_name, last_name=last_name)
    await message.answer("Привет! Этот под предназначен выдачи уведомлений о предстоящих событиях.")


class InsertForm(StatesGroup):
    waiting_for_name = State()          # Ожидание имени
    waiting_for_last_name = State()     # Ожидание фамилии
    waiting_for_birthday = State()      # Ожидание даты рождения
    waiting_for_description = State()   # Ожидание описания


class EditEventForm(StatesGroup):
    waiting_for_edits = State()  # Ожидание редактирования данных

# Обработчик команды /insert


@dp.message_handler(commands=['insert'])
async def cmd_insert(message: types.Message):
    """
    Команда /insert начинает заполнение формы.
    """
    await message.answer("Давайте добавим дату рождения.\nВведите имя:")
    await InsertForm.waiting_for_name.set()

# Обработчики состояний для заполнения формы


@dp.message_handler(state=InsertForm.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.reply("Отлично! Теперь введите фамилию:")
    await InsertForm.waiting_for_last_name.set()


@dp.message_handler(state=InsertForm.waiting_for_last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['last_name'] = message.text
    await message.reply("Отлично! Теперь введите дату рождения в формате ГГГГ-ММ-ДД (например, 1990-05-15):")
    await InsertForm.waiting_for_birthday.set()


@dp.message_handler(state=InsertForm.waiting_for_birthday)
async def process_birthday(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['birthday'] = datetime.strptime(message.text, '%Y-%m-%d')
            await message.reply("Отлично! Теперь введите описание или что-то еще:")
            await InsertForm.waiting_for_description.set()
        except ValueError:
            await message.reply("Неправильный формат даты. Пожалуйста, используйте формат ГГГГ-ММ-ДД.")


@dp.message_handler(state=InsertForm.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text

    # Здесь вы можете вызвать функцию insert_birthday и добавить данные в базу
    insert_event(
        first_name=data['name'],
        last_name=data['last_name'],
        birthday=data['birthday'],
        description=data['description']
    )

    await message.reply("Данные успешно добавлены в базу!")
    await state.finish()

# Обработчик команды /list


@dp.message_handler(commands=['list'])
async def list_events(message: types.Message):
    events = get_events()

    if not events:
        await message.answer("Список событий пуст.")
        return

    for event in events:
        event_text = f"Имя: {event['name']}\nФамилия: {event['last_name']}\nДата рождения: {event['birthday']}\nОписание: {event['description']}"
        keyboard = types.InlineKeyboardMarkup()
        edit_button = types.InlineKeyboardButton(
            "Редактировать", callback_data=f"edit_event_{event['id']}")
        delete_button = types.InlineKeyboardButton(
            "Удалить", callback_data=f"delete_event_{event['id']}")
        keyboard.add(edit_button, delete_button)
        await message.answer(event_text, reply_markup=keyboard)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('edit_event_'))
async def edit_event(callback_query: types.CallbackQuery, state: FSMContext):
    event_id = int(callback_query.data.split('_')[2])

    # Получаем данные о событии по его ID, используя вашу функцию get_event_by_id(event_id)
    event = get_event_by_id(event_id)
    print(event, type(event))
    if event:
        # Здесь можно отправить сообщение с данными события для редактирования
        message_text = f"Редактирование события ID {event_id}:\n"
        message_text += f"Имя: {event[1]}\n"
        message_text += f"Фамилия: {event[2]}\n"
        message_text += f"Дата рождения: {event[3]}\n"
        message_text += f"Описание: {event[4]}\n"
        message_text += "Введите новые значения через перенос строки (или оставьте пустым, чтобы не изменять):\n"

        # Отправляем сообщение для редактирования события
        await bot.send_message(callback_query.from_user.id, message_text)

        # Устанавливаем состояние для ожидания новых данных о событии
        await EditEventForm.waiting_for_edits.set()

        # Сохраняем ID редактируемого события в состоянии FSM
        async with state.proxy() as data:
            data['event_id'] = event_id
    else:
        # Если событие с указанным ID не найдено, отправляем сообщение об ошибке
        await bot.send_message(callback_query.from_user.id, f"Событие с ID {event_id} не найдено.")


# Обработчик состояния для ожидания новых данных о событии
@dp.message_handler(state=EditEventForm.waiting_for_edits)
async def process_edits(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        event_id = data['event_id']

        # Разбираем сообщение на новые значения
        new_values = message.text.split('\n')

        # Получаем текущие данные о событии
        event = get_event_by_id(event_id)
        event_data = list(event)

        # Обновляем значения в списках
        # Обновляем имя
        event_data[1] = new_values[0] if new_values[0] else event_data[1]
        # Обновляем фамилию
        event_data[2] = new_values[1] if new_values[1] else event_data[2]
        try:
            # Пытаемся преобразовать введенную дату рождения в формат datetime
            new_birthday = datetime.strptime(new_values[2], '%Y-%m-%d')
            event_data[3] = new_birthday  # Обновляем дату рождения
        except ValueError:
            pass  # Если введена неправильная дата, оставляем текущее значение
        # Обновляем описание
        event_data[4] = new_values[3] if new_values[3] else event_data[4]

        # Преобразуем список обратно в кортеж
        event_updated = tuple(event_data)
        # Здесь можно вызвать функцию для обновления данных в базе данных, например, update_event(event_id, event_updated)
        update_event(event_id, event_updated)

        # Отправляем сообщение с подтверждением обновления данных
        await bot.send_message(message.from_user.id, f"Данные события ID {event_id} успешно обновлены.")

        # Сбрасываем состояние
        await state.finish()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('delete_event_'))
async def delete_event(callback_query: types.CallbackQuery):
    event_id = int(callback_query.data.split('_')[2])
    if await perform_delete_event(event_id):
        await bot.send_message(callback_query.from_user.id, f"Событие ID {event_id} успешно удалено.")
    else:
        await bot.send_message(callback_query.from_user.id, f"Произошла ошибка при удалении события ID {event_id}.")


async def generate_event_tomorrow_message():
    events_tomorrow = await get_event_for_tomorrow()
    if events_tomorrow:
        message_text_tomorrow = "\nЗавтра есть следующие события:\n"
        for event in events_tomorrow:
            if event[4] == "День рождение":
                message_text_tomorrow += f"\n🟩 {event[4]} у {event[1]}\n"
            elif event[4] == "Оплата":
                message_text_tomorrow += f"\n🔴 {event[4]} за {event[1]}\n"
        return message_text_tomorrow


async def generate_event_week_message():
    events_week = await get_event_for_week()
    if events_week:
        message_text_week = "\nЧерез неделю следующие события:\n"
        for event in events_week:
            if event[4] == "День рождения":
                message_text_week += f"\n🟩 {event[4]} у {event[1]}\n"
            elif event[4] == "Оплата":
                message_text_week += f"\n🔴 {event[4]} за {event[1]}\n"
        return message_text_week


async def generate_event_today_message():
    events_today = await get_event_for_today()
    if events_today:
        message_text_today = "\nСегодня следующие события:\n"
        for event in events_today:
            if event[4] == "День рождение":
                message_text_today += f"\n🟩 {event[4]} у {event[1]}\n"
            elif event[4] == "Оплата":
                message_text_today += f"\n🔴 {event[4]} за {event[1]}\n"
        return message_text_today


async def scheduled_job():
    while True:
        now = datetime.now()
        if now.hour == 9 and now.minute == 0:
            finally_message_text = ""
            message_text_tomorrow = await generate_event_tomorrow_message()
            meesage_text_week = await generate_event_week_message()
            meesage_text_today = await generate_event_today_message()
            if message_text_tomorrow:
                finally_message_text += meesage_text_today
            if message_text_tomorrow:
                finally_message_text += message_text_tomorrow
            if meesage_text_week:
                finally_message_text += meesage_text_week
            try:
                await bot.send_message(chat_id=os.getenv("CHAT_ID"), text=finally_message_text)
            except Exception as e:
                print(f"Произошла ошибка при отправке сообщения: {e}")
        await asyncio.sleep(60)


if __name__ == '__main__':
    from aiogram import executor

    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_job())

    executor.start_polling(dp, skip_updates=True)

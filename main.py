from aiogram.utils import executor
from aiogram import Bot, types
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from datetime import datetime
from dotenv import load_dotenv
from models import new_bot_users, insert_birthday

import os
import logging



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
    await message.answer("Привет!")

class InsertForm(StatesGroup):
    waiting_for_name = State()          # Ожидание имени
    waiting_for_last_name = State()     # Ожидание фамилии
    waiting_for_birthday = State()      # Ожидание даты рождения
    waiting_for_description = State()   # Ожидание описания

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
    insert_birthday(
        first_name=data['name'],
        last_name=data['last_name'],
        birthday=data['birthday'],
        description=data['description']
    )

    await message.reply("Данные успешно добавлены в базу!")
    await state.finish()


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)

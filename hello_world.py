import os
import asyncio

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

from keyboards import main_keyboard

VERSION = os.getenv("APP_VERSION", "unknown")

# Загружаем переменные из .env файла
load_dotenv()

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Hello World!", 
        reply_markup=main_keyboard(),
        )


@dp.message(Command("hello"))
async def cmd_hello(message: types.Message):
    await message.answer("Hello World!")

@dp.callback_query(F.data == "get_numbers")
async def on_numbers(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("Ты нажал Numbers")

@dp.callback_query(F.data == "get_abs")
async def on_abs(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("Ты нажал Abs")


async def main():
    print(f"🚀 Bot starting, version={VERSION}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

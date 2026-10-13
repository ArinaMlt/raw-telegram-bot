import os
import asyncio

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

from handlers import router
from keyboards import main_keyboard, main_reply_keyboard

VERSION = os.getenv("APP_VERSION", "unknown")

# Загружаем переменные из .env файла
load_dotenv()

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(router)


async def main():
    print(f"🚀 Bot starting, version={VERSION}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

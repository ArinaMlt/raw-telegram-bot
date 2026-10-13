import os
import asyncio

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from handlers import router

VERSION = os.getenv("APP_VERSION", "unknown")

# Загружаем переменные из .env файла
load_dotenv()

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(router)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="hello", description="Поздороваться"),
        BotCommand(command="start_2", description="Показать кнопки"),
        BotCommand(command="settings", description="Настройки"),
    ]
    await bot.set_my_commands(commands)


async def main():
    print(f"🚀 Bot starting, version={VERSION}")
    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

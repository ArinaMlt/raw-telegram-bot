import os
import asyncio

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from handlers import router
from habit_tracker import router as habits_router, init_db, reminder_loop

VERSION = os.getenv("APP_VERSION", "unknown")

# Загружаем переменные из .env файла
load_dotenv()

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(router)
dp.include_router(habits_router)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="hello", description="Поздороваться"),
        BotCommand(command="start_2", description="Показать кнопки"),
        BotCommand(command="settings", description="Настройки"),
    ]
    await bot.set_my_commands(commands)


async def main():
    init_db()

    print(f"🚀 Bot starting, version={VERSION}")
    await set_commands(bot)

    reminder_task = asyncio.create_task(reminder_loop(bot))

    try:
        await dp.start_polling(bot)
    finally:
        reminder_task.cancel()
        try:
            await reminder_task
        except asyncio.CancelledError:
            pass



if __name__ == "__main__":
    asyncio.run(main())

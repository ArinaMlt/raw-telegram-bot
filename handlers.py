import asyncio

from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from keyboards import main_reply_keyboard, main_keyboard

router = Router()

async def delayed_message(bot, chat_id: int, text: str, delay: int = 60):
    """Отправить сообщение через delay секунд в фоне."""
    try:
        await asyncio.sleep(delay)
        await bot.send_message(chat_id, text)
    except Exception as e:
        print(f"❌ delayed_message failed: {e}")

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer('Запуск сообщения по команде /start используя фильтр CommandStart()')

@router.message(Command("start_2"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Выбери, что запросить:",
        reply_markup=main_reply_keyboard(),
    )

@router.message(F.text == "📊 Numbers")
async def on_numbers(message: types.Message):
    await message.answer("Ты нажал Numbers")


@router.message(Command("hello"))
async def cmd_hello(message: types.Message):
    await message.answer(
            "Hello World!", 
            reply_markup=main_keyboard(),
            )

@router.callback_query(F.data == "get_numbers")
async def on_numbers(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("Ты нажал Numbers")

@router.callback_query(F.data == "get_abs")
async def on_abs(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("Ты нажал Abs")

@router.message(F.text == "📊 Главное меню")
async def on_numbers(message: types.Message):
    await message.answer("Ты нажал One")


@router.message(F.text == "⚙️ Настройки")
async def on_settings(message: types.Message):
    await message.answer("Настройки открыты. Через минуту придёт уведомление.")
    asyncio.create_task(
        delayed_message(
            bot=message.bot,
            chat_id=message.chat.id,
            text="прошла 1 минута",
            delay=60,
        )
    )
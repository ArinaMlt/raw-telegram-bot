from aiogram.types import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопками."""
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Numbers", callback_data="get_numbers")
    kb.button(text="🔤 Abs", callback_data="get_abs")
    kb.adjust(2)
    return kb.as_markup()

def main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply-клавиатура — кнопки внизу экрана."""
    kb = ReplyKeyboardBuilder()
    kb.button(text="📊 Главное меню")
    kb.button(text="⚙️ Настройки")
    kb.button(text="🌱 Привычки")
    kb.adjust(2, 1)
    return kb.as_markup(
        resize_keyboard=True,   # компактный размер, не растягивается на всю ширину
        one_time_keyboard=True,  # исчезает после первого нажатия
        input_field_placeholder="Воспользуйтесь меню:"
    )

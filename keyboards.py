from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопками."""
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Numbers", callback_data="get_numbers")
    kb.button(text="🔤 Abs", callback_data="get_abs")
    kb.adjust(2)
    return kb.as_markup()

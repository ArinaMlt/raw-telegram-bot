
import asyncio
import os
import sqlite3

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder


router = Router()

DB_FILE = Path("habits.db")

DAYS = {
    "пн": 0,
    "вт": 1,
    "ср": 2,
    "чт": 3,
    "пт": 4,
    "сб": 5,
    "вс": 6,
}

DAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def now_local() -> datetime:
    timezone = ZoneInfo(os.getenv("TIMEZONE", "Europe/Moscow"))
    return datetime.now(timezone)


def get_connection():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with get_connection() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                days TEXT NOT NULL,
                reminder_time TEXT,
                active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS habit_completions (
                habit_id INTEGER NOT NULL,
                completion_date TEXT NOT NULL,
                PRIMARY KEY (habit_id, completion_date),
                FOREIGN KEY (habit_id)
                    REFERENCES habits(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sent_reminders (
                habit_id INTEGER NOT NULL,
                reminder_date TEXT NOT NULL,
                PRIMARY KEY (habit_id, reminder_date),
                FOREIGN KEY (habit_id)
                    REFERENCES habits(id) ON DELETE CASCADE
            );
        """)


class AddHabit(StatesGroup):
    name = State()
    days = State()
    reminder_time = State()


def main_habits_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить привычку", callback_data="habits:add")
    kb.button(text="📋 Мои привычки", callback_data="habits:list")
    kb.button(text="📊 Статистика", callback_data="habits:stats")
    kb.adjust(1)
    return kb.as_markup()


@router.message(F.text == "🌱 Привычки")
async def open_habits_menu(message: types.Message):
    await message.answer(
        "🌱 Трекер привычек\nВыбери действие:",
        reply_markup=main_habits_keyboard(),
    )


def list_keyboard(habits, today: str):
    kb = InlineKeyboardBuilder()

    for habit in habits:
        with get_connection() as db:
            completed = db.execute(
                """
                SELECT 1 FROM habit_completions
                WHERE habit_id = ? AND completion_date = ?
                """,
                (habit["id"], today),
            ).fetchone()

        mark = "✅" if completed else "⬜"
        kb.button(
            text=f"{mark} {habit['name']}",
            callback_data=f"habit:done:{habit['id']}",
        )

    kb.button(text="➕ Добавить привычку", callback_data="habits:add")
    kb.button(text="📊 Статистика", callback_data="habits:stats")
    kb.adjust(1)
    return kb.as_markup()


def get_user_habits(user_id: int):
    with get_connection() as db:
        return db.execute(
            """
            SELECT * FROM habits
            WHERE user_id = ? AND active = 1
            ORDER BY id
            """,
            (user_id,),
        ).fetchall()


def is_scheduled(habit, day: date) -> bool:
    if habit["days"] == "daily":
        return True

    selected_days = {
        int(value)
        for value in habit["days"].split(",")
        if value
    }
    return day.weekday() in selected_days


@router.message(Command("habits"))
async def open_habits_command(message: types.Message):
    await message.answer(
        "🌱 Трекер привычек\nВыбери действие:",
        reply_markup=main_habits_keyboard(),
    )


@router.callback_query(F.data == "habits:add")
async def start_add_habit(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    await state.clear()
    await state.set_state(AddHabit.name)

    await callback.message.answer(
        "Как назовём привычку?\n"
        "Например: Читать 10 страниц."
    )
    await callback.answer()


@router.message(AddHabit.name)
async def enter_habit_name(
    message: types.Message,
    state: FSMContext,
):
    name = (message.text or "").strip()

    if not name or len(name) > 100:
        await message.answer(
            "Название должно содержать от 1 до 100 символов."
        )
        return

    await state.update_data(name=name)
    await state.set_state(AddHabit.days)

    await message.answer(
        "Как часто выполнять привычку?\n\n"
        "Напиши «каждый день» или перечисли дни недели:\n"
        "пн,ср,пт"
    )


@router.message(AddHabit.days)
async def enter_habit_days(
    message: types.Message,
    state: FSMContext,
):
    value = (message.text or "").strip().lower()

    if value in ("каждый день", "ежедневно", "daily"):
        days = "daily"
    else:
        parts = [
            part.strip().replace(".", "")
            for part in value.replace(" ", "").split(",")
        ]

        if not parts or any(part not in DAYS for part in parts):
            await message.answer(
                "Не поняла расписание.\n"
                "Введи «каждый день» или, например, пн,ср,пт."
            )
            return

        days = ",".join(
            str(DAYS[part]) for part in sorted(
                set(parts), key=lambda part: DAYS[part]
            )
        )

    await state.update_data(days=days)
    await state.set_state(AddHabit.reminder_time)

    await message.answer(
        "Во сколько напоминать?\n"
        "Напиши время в формате 20:00.\n"
        "Если уведомление не нужно, напиши «нет»."
    )


@router.message(AddHabit.reminder_time)
async def enter_habit_time(
    message: types.Message,
    state: FSMContext,
):
    value = (message.text or "").strip().lower()

    if value in ("нет", "без напоминания", "не нужно"):
        reminder_time = None
    else:
        try:
            reminder_time = datetime.strptime(
                value, "%H:%M"
            ).strftime("%H:%M")
        except ValueError:
            await message.answer(
                "Укажи время, например 20:00, или напиши «нет»."
            )
            return

    data = await state.get_data()

    with get_connection() as db:
        db.execute(
            """
            INSERT INTO habits (user_id, name, days, reminder_time)
            VALUES (?, ?, ?, ?)
            """,
            (
                message.from_user.id,
                data["name"],
                data["days"],
                reminder_time,
            ),
        )

    await state.clear()

    schedule = (
        "каждый день"
        if data["days"] == "daily"
        else ", ".join(
            DAY_NAMES[int(day)] for day in data["days"].split(",")
        )
    )

    notification = (
        f"Напоминание: {reminder_time}"
        if reminder_time
        else "Без уведомлений"
    )

    await message.answer(
        f"✅ Привычка «{data['name']}» сохранена!\n"
        f"Расписание: {schedule}\n"
        f"{notification}",
        reply_markup=main_habits_keyboard(),
    )


@router.callback_query(F.data == "habits:list")
async def show_habits(callback: types.CallbackQuery):
    today = now_local().date()
    habits = get_user_habits(callback.from_user.id)

    if not habits:
        await callback.message.answer(
            "Пока привычек нет. Добавь первую!",
            reply_markup=main_habits_keyboard(),
        )
    else:
        today_text = today.isoformat()
        scheduled_habits = [
            habit for habit in habits
            if is_scheduled(habit, today)
        ]

        if not scheduled_habits:
            text = "На сегодня привычек по расписанию нет."
        else:
            text = "🌱 Привычки на сегодня:\nНажми на привычку, чтобы отметить выполнение."

        await callback.message.answer(
            text,
            reply_markup=list_keyboard(scheduled_habits, today_text),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("habit:done:"))
async def complete_habit(callback: types.CallbackQuery):
    habit_id = int(callback.data.split(":")[2])
    today = now_local().date()

    with get_connection() as db:
        habit = db.execute(
            """
            SELECT * FROM habits
            WHERE id = ? AND user_id = ? AND active = 1
            """,
            (habit_id, callback.from_user.id),
        ).fetchone()

        if habit is None:
            await callback.answer("Привычка не найдена.", show_alert=True)
            return

        if not is_scheduled(habit, today):
            await callback.answer("Сегодня эта привычка не запланирована.")
            return

        existing = db.execute(
            """
            SELECT 1 FROM habit_completions
            WHERE habit_id = ? AND completion_date = ?
            """,
            (habit_id, today.isoformat()),
        ).fetchone()

        if existing:
            await callback.answer("Уже отмечено! Повторно не засчитываю.")
            return

        db.execute(
            """
            INSERT INTO habit_completions (habit_id, completion_date)
            VALUES (?, ?)
            """,
            (habit_id, today.isoformat()),
        )

    await callback.answer("✅ Привычка выполнена!")
    await callback.message.answer(
        f"Отлично! «{habit['name']}» выполнена сегодня 🎉"
    )


@router.callback_query(F.data == "habits:stats")
async def show_stats(callback: types.CallbackQuery):
    today = now_local().date()
    habits = get_user_habits(callback.from_user.id)

    if not habits:
        await callback.message.answer(
            "Сначала добавь хотя бы одну привычку."
        )
        await callback.answer()
        return

    lines = ["📊 Статистика за последние 7 дней\n"]

    with get_connection() as db:
        for habit in habits:
            scheduled_dates = [
                today - timedelta(days=offset)
                for offset in range(7)
                if is_scheduled(habit, today - timedelta(days=offset))
            ]

            if not scheduled_dates:
                continue

            completed_dates = db.execute(
                """
                SELECT completion_date FROM habit_completions
                WHERE habit_id = ? AND completion_date >= ?
                    AND completion_date <= ?
                """,
                (
                    habit["id"],
                    min(scheduled_dates).isoformat(),
                    today.isoformat(),
                ),
            ).fetchall()

            completed_set = {
                row["completion_date"] for row in completed_dates
            }
            done_count = sum(
                day.isoformat() in completed_set
                for day in scheduled_dates
            )
            percent = round(done_count / len(scheduled_dates) * 100)

            # Считаем последовательные выполненные запланированные дни.
            streak = 0
            for offset in range(365):
                day = today - timedelta(days=offset)

                if not is_scheduled(habit, day):
                    continue

                if day.isoformat() not in completed_set:
                    # Для длинных серий загружаем недостающие отметки.
                    if offset >= 7:
                        row = db.execute(
                            """
                            SELECT 1 FROM habit_completions
                            WHERE habit_id = ? AND completion_date = ?
                            """,
                            (habit["id"], day.isoformat()),
                        ).fetchone()
                        if row:
                            streak += 1
                            continue
                    break

                streak += 1

            lines.append(
                f"• {habit['name']}\n"
                f"  Выполнено: {done_count}/{len(scheduled_dates)} "
                f"({percent}%)\n"
                f"  Серия: {streak} дн.\n"
            )

    await callback.message.answer("\n".join(lines))
    await callback.answer()


async def reminder_loop(bot: Bot):
    """Отправляет индивидуальные напоминания по расписанию."""

    while True:
        now = now_local()
        today = now.date()
        current_time = now.strftime("%H:%M")

        with get_connection() as db:
            habits = db.execute(
                """
                SELECT * FROM habits
                WHERE active = 1 AND reminder_time = ?
                """,
                (current_time,),
            ).fetchall()

        for habit in habits:
            if not is_scheduled(habit, today):
                continue

            with get_connection() as db:
                already_sent = db.execute(
                    """
                    SELECT 1 FROM sent_reminders
                    WHERE habit_id = ? AND reminder_date = ?
                    """,
                    (habit["id"], today.isoformat()),
                ).fetchone()

            if already_sent:
                continue

            try:
                await bot.send_message(
                    habit["user_id"],
                    f"🔔 Напоминание о привычке:\n"
                    f"{habit['name']}\n\n"
                    "Когда выполнишь, отметь её в боте.",
                )

                with get_connection() as db:
                    db.execute(
                        """
                        INSERT OR IGNORE INTO sent_reminders
                            (habit_id, reminder_date)
                        VALUES (?, ?)
                        """,
                        (habit["id"], today.isoformat()),
                    )
            except Exception as error:
                print(
                    f"Не удалось отправить напоминание "
                    f"для привычки {habit['id']}: {error}"
                )

        await asyncio.sleep(20)

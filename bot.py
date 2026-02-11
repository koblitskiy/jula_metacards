import os
import random
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = "8480568700:AAEOABkovhrTSwcFhmjIRLKFHAIKS7p33cY"
PRACTITIONER_ID = 575159735  # ← твой Telegram ID
CHANNEL_URL = "https://t.me/mac_jula_bot"
CHANNEL_ID = "@belike_jula"
CARDS_PATH = os.path.join(os.path.dirname(__file__), "cards")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    session=AiohttpSession()
)
dp = Dispatcher()

# ---------------- FSM ----------------
class UserState(StatesGroup):
    choosing_sphere = State()
    waiting_card = State()

# ---------------- Сферы ----------------
SPHERES = {
    "work": "💼 Работа",
    "relationships": "❤️ Отношения",
    "health": "🧘 Здоровье",
    "move": "🌍 Переезд",
    "finance": "💰 Финансы"
}

# ---------------- Активные пользователи ----------------
active_users = {}  # user_id → username

# ---------------- Главное меню ----------------
main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📋 Меню", callback_data="open_menu")]
])

# ---------------- Подменю ----------------
menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🃏 Взять карту", callback_data="menu_card")],
    [InlineKeyboardButton(text="✏️ Написать лично", url="https://t.me/YOUR_USERNAME")],
    [InlineKeyboardButton(text="🔗 Перейти на канал", url=CHANNEL_URL)],
    [InlineKeyboardButton(text="🎮 Записаться на игру", callback_data="menu_game")]
])

# ---------------- Кнопка после карты ----------------
card_questions_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✏️ Написать лично", url="https://t.me/YOUR_USERNAME")]
])

# ================= Начало =================
@dp.message(Command(commands=["start", "play"]))
async def start_game(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Перейти в канал", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")]
    ])
    await message.answer(
        "Привет ✨\n\n"
        "Добро пожаловать в пространство метафорических карт!\n\n"
        "Чтобы продолжить, подпишись на канал 👇",
        reply_markup=keyboard
    )

# ---------------- Проверка подписки ----------------
@dp.callback_query(lambda c: c.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"sphere_{key}")]
            for key, name in SPHERES.items()
        ]
    )
    await state.set_state(UserState.choosing_sphere)
    await callback.message.answer(
        "Выбери сферу, с которой хочешь поработать сейчас:",
        reply_markup=keyboard
    )

# ---------------- Выбор сферы ----------------
@dp.callback_query(lambda c: c.data.startswith("sphere_"))
async def choose_sphere(callback: types.CallbackQuery, state: FSMContext):
    sphere_key = callback.data.replace("sphere_", "")
    await state.update_data(sphere=sphere_key)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎴 Получить карту", callback_data="get_card")]
        ]
    )

    await state.set_state(UserState.waiting_card)
    await callback.message.answer(
        "Сейчас ты получишь свою метафорическую карту.\n\n"
        "Посмотри на неё и подумай, как она отражает твоё текущее состояние.\n"
        "Что ты в ней видишь?",
        reply_markup=keyboard
    )

# ---------------- Получение карты ----------------
@dp.callback_query(lambda c: c.data == "get_card")
async def send_card(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sphere = data["sphere"]

    folder = os.path.join(CARDS_PATH, sphere)
    files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png'))] if os.path.exists(folder) else []

    if not files:
        await callback.message.answer(
            "✨ Карты пока нет в этой категории.\n"
            "Опиши своё текущее состояние — и мы разберём это вместе!"
        )
        card_name = "no_card"
    else:
        card_name = random.choice(files)
        file_path = os.path.join(folder, card_name)
        if os.path.exists(file_path):
            await callback.message.answer_photo(photo=types.FSInputFile(file_path))
        else:
            await callback.message.answer("❌ Ошибка: не удалось загрузить карту.")

    await state.update_data(card=card_name)

    # Показываем 3 вопроса с описанием вместо поля ввода
    questions_text = (
        "Вопрос 1\nВопрос 2\nВопрос 3\n\n"
        "Описание: карта дана вам не просто так — она точно что-то для вас значит. "
        "Если самому понять сложно, давай разберемся вместе."
    )
    await callback.message.answer(questions_text, reply_markup=card_questions_kb)

# ---------------- Подменю "Меню" ----------------
@dp.callback_query(lambda c: c.data == "open_menu")
async def open_menu(callback: types.CallbackQuery):
    await callback.message.answer("Выберите действие 👇", reply_markup=menu_kb)

@dp.callback_query(lambda c: c.data == "menu_card")
async def menu_get_card(callback: types.CallbackQuery):
    # Просто перенаправляем пользователя к выбору сферы
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"sphere_{key}")]
            for key, name in SPHERES.items()
        ]
    )
    await callback.message.answer("Выбери сферу для работы:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "menu_game")
async def register_game(callback: types.CallbackQuery):
    await callback.message.answer("🎮 Вы успешно записались на игру! Мы свяжемся с вами для подтверждения.")

# ---------------- Запуск бота ----------------
async def main():
    print("Бот запущен 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

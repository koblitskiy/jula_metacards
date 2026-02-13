import os
import random
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ForceReply
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = "8480568700:AAEOABkovhrTSwcFhmjIRLKFHAIKS7p33cY"
PRACTITIONER_ID = 575159735  # ← твой Telegram ID
CHANNEL_URL = "https://t.me/mac_jula_bot"
CARDS_PATH = os.path.join(os.path.dirname(__file__), "cards")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    session=AiohttpSession()
)
dp = Dispatcher()

# ---------------- FSM ----------------
class UserState(StatesGroup):
    waiting_card = State()  # состояние после подготовки

# ---------------- Игры ----------------
GAMES = {
    "abundance": "🔑 Ключ к изобилию",
    "inner_map": "🗺 Карта внутреннего мира",
    "advice": "💡 Нужен совет"
}

# ---------------- Активные пользователи ----------------
active_users = {}  # user_id → username

# ---------------- Главное меню ----------------
main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Меню")]
    ],
    resize_keyboard=True
)

# ---------------- Подменю ----------------
menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎴 Получить карту", callback_data="prepare_card")],
    [InlineKeyboardButton(text="✏️ Написать лично", url="https://t.me/belike_jula")],
    [InlineKeyboardButton(text="🔗 Перейти на канал", url="https://t.me/tigra_jula")],
    [InlineKeyboardButton(text="🎮 Записаться на игру", callback_data="menu_game")]
])

# ---------------- Кнопка после карты ----------------
card_questions_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✏️ Написать лично", url="https://t.me/belike_jula")],
    [InlineKeyboardButton(text="🎴 Получить новую карту", callback_data="prepare_card")]
])

# ================= Начало =================
@dp.message(Command(commands=["start", "play"]))
async def start_game(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Перейти в канал", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="✅ Хочу взять карту", callback_data="prepare_card")]
    ])
    await message.answer(
        "Привет ✨\n\n"
        "Добро пожаловать в пространство метафорических карт!\n\n"
        "Чтобы продолжить, подпишись на канал 👇",
        reply_markup=keyboard
    )
    # Показываем кнопку меню
    await message.answer("Тут есть меню 👇", reply_markup=main_menu_kb)

# ---------------- Этап подготовки перед картой ----------------
@dp.callback_query(lambda c: c.data == "prepare_card")
async def prepare_card(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎴 Получить карту", callback_data="get_card")]
        ]
    )
    await callback.message.answer(
        "🌟 Настройся на получение карты.\n"
        "Сделай глубокий вдох, сосредоточься на себе и подумай о том, "
        "что сейчас волнует тебя больше всего.",
        reply_markup=keyboard
    )

# ---------------- Получение карты ----------------
@dp.callback_query(lambda c: c.data == "get_card")
async def send_card(callback: types.CallbackQuery, state: FSMContext):
    folder = CARDS_PATH
    files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png'))] if os.path.exists(folder) else []

    if not files:
        await callback.message.answer(
            "✨ Карты пока нет.\n"
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

    # Показываем вопросы после карты + кнопку новой карты
    questions_text = (
        "Вопрос 1\nВопрос 2\nВопрос 3\n\n"
        "Описание: карта дана вам не просто так — давайте думайте, решайте, полюбому у вас проблемы с головой или ещё с чем-то."
    )
    await callback.message.answer(questions_text, reply_markup=card_questions_kb)

# ---------------- Подменю "Меню" ----------------
@dp.message(lambda m: m.text == "📋 Меню")
async def open_menu(message: types.Message):
    await message.answer("Выберите действие 👇", reply_markup=menu_kb)

# ---------------- Кнопка "Записаться на игру" ----------------
@dp.callback_query(lambda c: c.data == "menu_game")
async def menu_game(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"game_{key}")]
            for key, name in GAMES.items()
        ]
    )
    await callback.message.answer("Выберите игру, в которой хотите принять участие:", reply_markup=keyboard)

# ---------------- Выбор конкретной игры ----------------
@dp.callback_query(lambda c: c.data.startswith("game_"))
async def choose_game(callback: types.CallbackQuery):
    game_key = callback.data.replace("game_", "")
    game_name = GAMES.get(game_key, "Неизвестная игра")

    user_id = callback.from_user.id
    username = callback.from_user.username or str(user_id)
    active_users[user_id] = username  # сохраняем для ответа

    # Сообщение клиенту
    await callback.message.answer("Вы на пути к лучшей версии себя, скоро отвечу!")

    # Сообщение игропрактику
    text = (
        f"🎮 <b>Новый участник игры</b>\n\n"
        f"👤 Пользователь: @{username} ({user_id})\n"
        f"🕹 Игра: {game_name}"
    )
    reply_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏ Ответить пользователю", callback_data=f"reply_game_{user_id}")]
        ]
    )
    await bot.send_message(PRACTITIONER_ID, text, reply_markup=reply_kb)

# ---------------- Игропрактик отвечает ----------------
@dp.callback_query(lambda c: c.data.startswith("reply_game_"))
async def reply_game(callback: types.CallbackQuery):
    user_id = int(callback.data.replace("reply_game_", ""))
    await callback.message.answer(
        f"🖊 Напиши ответ пользователю @{active_users.get(user_id, user_id)}:",
        reply_markup=ForceReply(input_field_placeholder="Введите ответ...")
    )

# ---------------- Запуск бота ----------------
async def main():
    print("Бот запущен 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

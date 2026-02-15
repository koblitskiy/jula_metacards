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
CHANNEL_URL = "https://t.me/tigra_jula"
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
    [InlineKeyboardButton(text="🔗 Перейти на канал", url=CHANNEL_URL)],
    [InlineKeyboardButton(text="🎮 Записаться на игру", callback_data="menu_game")]
])

# ---------------- Кнопки после карты ----------------
post_card_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔗 Перейти на канал", url=CHANNEL_URL)],
    [InlineKeyboardButton(text="🎮 Хочу на Т-Игру", callback_data="want_game")],
    [InlineKeyboardButton(text="🎴 Получить новую карту", callback_data="prepare_card")]
])

# ================= Начало =================
@dp.message(Command(commands=["start", "play"]))
async def start_game(message: types.Message):
    welcome_text = (
        "✨ <b>Добро пожаловать в пространство метафорических карт</b> ✨\n\n"
        "Вы вошли в безопасное пространство для самопознания и осознанного исследования своих мыслей, эмоций и переживаний. "
        "Здесь вы сможете наблюдать свои ощущения, находить новые инсайты и лучше понимать себя, "
        "используя метафорические карты как осознание для рефлексии и личного роста."
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Перейти в канал", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="✅ Хочу взять карту", callback_data="prepare_card")]
    ])
    await message.answer(welcome_text, reply_markup=keyboard)
    await message.answer("Тут есть меню 👇", reply_markup=main_menu_kb)

# ---------------- Этап подготовки перед картой ----------------
@dp.callback_query(lambda c: c.data == "prepare_card")
async def prepare_card(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎴 Получить карту", callback_data="get_card")]
        ]
    )
    
    text = (
        "🧘‍♀️ <b>Настройка перед получением карты</b>\n\n"
        "Перед тем как получить карту, выполните следующие шаги:\n\n"
        "1️⃣ <b>Удобно сядьте</b> и закройте глаза на несколько секунд.\n"
        "2️⃣ <b>Сделайте</b> несколько глубоких вдохов и выдохов, отпуская напряжение.\n"
        "3️⃣ <b>Позвольте</b> себе на мгновение отойти от внешних забот и сосредоточиться на своих ощущениях здесь и сейчас.\n"
        "4️⃣ <b>Наблюдайте</b> за своими мыслями и эмоциями, не оценивая их, просто отмечайте.\n"
        "5️⃣ <b>Подумайте</b> о том, что в данный момент вызывает у вас наибольший интерес или беспокойство.\n\n"
        "✨ Эта карта будет вашим инструментом для понимания себя и ваших текущих переживаний.\n"
        "Примите её с открытым умом и доверьтесь своим ощущениям."
    )

    await callback.message.answer(text, reply_markup=keyboard)

# ---------------- Получение карты ----------------
@dp.callback_query(lambda c: c.data == "get_card")
async def send_card(callback: types.CallbackQuery, state: FSMContext):
    folder = CARDS_PATH
    files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png'))] if os.path.exists(folder) else []

    if not files:
        await callback.message.answer(
            "✨ Карты пока нет.\n"
            "Опишите своё текущее состояние — и мы разберём это вместе!"
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

    # ---------------- Мини-сессия после карты с атмосферным оформлением ----------------
    questions_text = (
        "✦✦✦ <b>Мини-сессия рефлексия</b> ✦✦✦\n\n"
        "💭 <b>Вопрос 1:</b> Что первое приходит вам на ум, когда вы смотрите на эту карту?\n\n"
        "💡 <b>Вопрос 2:</b> Какие эмоции или ощущения она у вас вызывает?\n\n"
        "🔍 <b>Вопрос 3:</b> Как эта карта может помочь вам понять текущую ситуацию или сделать следующий шаг?\n\n"
        "🌟 <i>Совет:</i> Отвечайте честно себе, без самокритики, наблюдайте свои внутренние реакции.\n"
        "🕯 Можно сделать небольшой перерыв, вдохнуть глубоко и записать мысли в блокнот."
    )

    await callback.message.answer(questions_text, reply_markup=post_card_kb)

# ---------------- Обработка нажатия "Хочу на Т-Игру" ----------------
@dp.callback_query(lambda c: c.data == "want_game")
async def user_wants_game(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or str(user_id)

    text = (
        f"🎮 <b>Новый запрос на игру</b>\n\n"
        f"👤 Пользователь: @{username} ({user_id})\n"
        f"🕹 Запросил участие в Т-Игре"
    )

    await bot.send_message(PRACTITIONER_ID, text)

    await callback.message.answer(
        "✅ Ваш запрос отправлен! Скоро с вами свяжется игропрактик."
    )

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

    await callback.message.answer("Вы на пути к лучшей версии себя, скоро отвечу!")

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
        f"🖊 Напишите ответ пользователю @{active_users.get(user_id, user_id)}:",
        reply_markup=ForceReply(input_field_placeholder="Введите ответ...")
    )

# ---------------- Запуск бота ----------------
async def main():
    print("Бот запущен 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())




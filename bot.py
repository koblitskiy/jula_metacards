import os
import random
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = "8324589135:AAHH1IVFYvq8NDy116bR2dGyqsft9sbQSX0"
PRACTITIONER_ID = 575159735  # ← твой Telegram ID
CHANNEL_URL = "https://t.me/tigra_jula"
CHANNEL_ID = "@belike_jula"

# Корневая папка с картами
CARDS_PATH = os.path.join(os.path.dirname(__file__), "cards")
# ===============================================

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
    waiting_text = State()

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

# ---------------- Начало игры ----------------
@dp.message(Command(commands=["start", "play"]))
async def start_game(message: types.Message, state: FSMContext):
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
    await state.set_state(UserState.waiting_text)

    await callback.message.answer(
        "Напиши, что ты видишь на карте.\n"
        "Я помогу тебе разобраться."
    )

# ---------------- Получение текста пользователя ----------------
@dp.message(UserState.waiting_text)
async def get_user_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username or str(user_id)

    active_users[user_id] = username

    # Кнопка Force Reply для игропрактика
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ответить пользователю", callback_data=f"force_reply_{user_id}")]
        ]
    )

    text = (
        f"🔔 <b>Новый запрос</b>\n\n"
        f"👤 Пользователь: @{username}\n"
        f"🎯 Сфера: {SPHERES.get(data['sphere'], 'Неизвестно')}\n"
        f"🎴 Карта: {data['card']}\n\n"
        f"💬 Ответ:\n{message.text}"
    )

    await bot.send_message(PRACTITIONER_ID, text, reply_markup=keyboard)
    await message.answer("Спасибо ✨ Я свяжусь с тобой совсем скоро.")
    await state.clear()

# ---------------- Игропрактик нажал кнопку "Ответить пользователю" ----------------
@dp.callback_query(lambda c: c.data.startswith("force_reply_"))
async def force_reply(callback: types.CallbackQuery):
    user_id = int(callback.data.replace("force_reply_", ""))
    await callback.message.answer(
        f"🖊 Напиши ответ пользователю @{active_users.get(user_id, user_id)}:",
        reply_markup=ForceReply(input_field_placeholder="Введите ответ...")
    )

# ---------------- Игропрактик прислал ответ через Force Reply ----------------
@dp.message()
async def send_reply(message: types.Message):
    if not message.reply_to_message:
        return  # Игнорируем обычные сообщения
    text = message.text
    # Определяем user_id из текста reply_to_message
    reply_text = message.reply_to_message.text
    # Ищем user_id в тексте
    import re
    match = re.search(r'user@?id?:?\s*(\d+)', reply_text)
    if match:
        user_id = int(match.group(1))
    else:
        # Если не нашли, пробуем по active_users
        for uid, username in active_users.items():
            if username in reply_text:
                user_id = uid
                break
        else:
            return

    try:
        await bot.send_message(user_id, f"💬 Ответ от игропрактика:\n\n{text}")
        await message.answer("✅ Ответ успешно отправлен пользователю.")
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить сообщение: {e}")

# ---------------- Запуск бота ----------------
async def main():
    print("Бот запущен 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


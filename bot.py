import os
import random
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ForceReply
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ТВОЙ_ТОКЕН_ОТ_BOTFATHER")
PRACTITIONER_ID = 575159735
CHANNEL_URL = "https://t.me/tigra_jula"
CARDS_PATH = os.path.join(os.path.dirname(__file__), "cards")

# ================== ИНИЦИАЛИЗАЦИЯ ==================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML), session=AiohttpSession())
dp = Dispatcher()
app = Flask(__name__)  # Flask-приложение для webhook

# ================== FSM ==================
class UserState(StatesGroup):
    waiting_question = State()

# ================== КЛАВИАТУРЫ ==================
main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📋 Меню")]],
    resize_keyboard=True
)

menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎴 Получить карту", callback_data="prepare_card")],
    [InlineKeyboardButton(text="🔗 Перейти на канал", url=CHANNEL_URL)],
    [InlineKeyboardButton(text="🎮 Хочу на Т-Игру", callback_data="want_game")]
])

post_card_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❓ Задать вопрос по карте", callback_data="ask_question")],
    [InlineKeyboardButton(text="🔗 Перейти на канал", url=CHANNEL_URL)],
    [InlineKeyboardButton(text="🎮 Хочу на Т-Игру", callback_data="want_game")],
    [InlineKeyboardButton(text="🎴 Получить новую карту", callback_data="prepare_card")]
])

# ================== ОБРАБОТЧИКИ ==================
@dp.message(Command(commands=["start"]))
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("🎴 Получить карту", callback_data="prepare_card")]])
    await message.answer("✨ Добро пожаловать в пространство метафорических карт!", reply_markup=keyboard)
    await message.answer("Меню 👇", reply_markup=main_menu_kb)

@dp.message(lambda m: m.text == "📋 Меню")
async def open_menu(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=menu_kb)

@dp.callback_query(lambda c: c.data == "prepare_card")
async def prepare_card(callback: types.CallbackQuery):
    text = (
        "🧘‍♀️ Подготовка перед получением карты:\n"
        "1️⃣ Удобно сядьте и закройте глаза\n"
        "2️⃣ Сделайте несколько глубоких вдохов\n"
        "3️⃣ Сосредоточьтесь на своих ощущениях\n"
        "4️⃣ Подумайте о вопросе, который хотите задать"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("✨ Получить карту", callback_data="get_card")]])
    await callback.message.answer(text, reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "get_card")
async def send_card(callback: types.CallbackQuery, state: FSMContext):
    files = [f for f in os.listdir(CARDS_PATH) if f.lower().endswith(('.jpg', '.png'))] if os.path.exists(CARDS_PATH) else []
    if not files:
        await callback.message.answer("❌ В папке cards нет изображений.")
        return

    card_name = random.choice(files)
    file_path = os.path.join(CARDS_PATH, card_name)
    await callback.message.answer_photo(types.FSInputFile(file_path))
    await state.update_data(card=card_name)

    reflection = (
        "━━━━━━━━━━━━━━\n✨ Мини-сессия рефлексии\n"
        "💭 Что приходит на ум?\n💡 Эмоции и ощущения\n🔍 Как карта помогает понять ситуацию"
    )
    await callback.message.answer(reflection, reply_markup=post_card_kb)

@dp.callback_query(lambda c: c.data == "want_game")
async def want_game(callback: types.CallbackQuery):
    user = callback.from_user
    text = f"🎮 Новый запрос на Т-Игру\n👤 @{user.username or user.id}\nID: {user.id}"
    await bot.send_message(PRACTITIONER_ID, text)
    await callback.message.answer("✅ Ваш запрос отправлен.")

@dp.callback_query(lambda c: c.data == "ask_question")
async def ask_question(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_question)
    await callback.message.answer("✍️ Напишите ваш вопрос по карте:", reply_markup=ForceReply(input_field_placeholder="Введите вопрос..."))

@dp.message(UserState.waiting_question)
async def receive_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    card_name = data.get("card")
    user = message.from_user
    question = message.text

    header = f"❓ Вопрос по карте\n👤 @{user.username or user.id}\nID: {user.id}\n📝 {question}"

    if card_name:
        file_path = os.path.join(CARDS_PATH, card_name)
        if os.path.exists(file_path):
            await bot.send_photo(PRACTITIONER_ID, types.FSInputFile(file_path), caption=header)
        else:
            await bot.send_message(PRACTITIONER_ID, header)
    else:
        await bot.send_message(PRACTITIONER_ID, header)

    reply_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("✏ Ответить пользователю", callback_data=f"reply_{user.id}")]])
    await bot.send_message(PRACTITIONER_ID, "Ответить:", reply_markup=reply_kb)
    await message.answer("✅ Вопрос отправлен.")
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith("reply_"))
async def reply_user(callback: types.CallbackQuery):
    user_id = int(callback.data.replace("reply_", ""))
    await callback.message.answer(f"🖊 Напишите ответ пользователю ({user_id}):", reply_markup=ForceReply())

@dp.message(lambda m: m.reply_to_message and "Напишите ответ пользователю" in m.reply_to_message.text)
async def send_answer(message: types.Message):
    user_id = int(message.reply_to_message.text.split("(")[1].replace("):", "").replace(")", ""))
    answer = f"━━━━━━━━━━━━━━\n✨ Ответ игропрактика\n{message.text}"
    after_answer_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🎴 Получить новую карту", callback_data="prepare_card")],
        [InlineKeyboardButton("🎮 Хочу на Т-Игру", callback_data="want_game")],
        [InlineKeyboardButton("🔗 Перейти на канал", url=CHANNEL_URL)]
    ])
    await bot.send_message(user_id, answer, reply_markup=after_answer_kb)
    await message.answer("✅ Ответ отправлен.")




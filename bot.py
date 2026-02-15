import os
import random
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ForceReply
)
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties


# ================== НАСТРОЙКИ ==================
BOT_TOKEN = "8480568700:AAEOABkovhrTSwcFhmjIRLKFHAIKS7p33cY"
PRACTITIONER_ID = 575159735  # Твой Telegram ID
CHANNEL_URL = "https://t.me/tigra_jula"
CARDS_PATH = os.path.join(os.path.dirname(__file__), "cards")


bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    session=AiohttpSession()
)
dp = Dispatcher()


# ================== FSM ==================
class UserState(StatesGroup):
    waiting_question = State()


# ================== ГЛАВНОЕ МЕНЮ ==================
main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Меню")]
    ],
    resize_keyboard=True
)

menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎴 Получить карту", callback_data="prepare_card")],
    [InlineKeyboardButton(text="🔗 Перейти на канал", url=CHANNEL_URL)],
    [InlineKeyboardButton(text="🎮 Хочу на Т-Игру", callback_data="want_game")]
])


# ================== КНОПКИ ПОСЛЕ КАРТЫ ==================
post_card_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❓ Задать вопрос по карте", callback_data="ask_question")],
    [InlineKeyboardButton(text="🔗 Перейти на канал", url=CHANNEL_URL)],
    [InlineKeyboardButton(text="🎮 Хочу на Т-Игру", callback_data="want_game")],
    [InlineKeyboardButton(text="🎴 Получить новую карту", callback_data="prepare_card")]
])


# ================== СТАРТ ==================
@dp.message(Command(commands=["start"]))
async def start(message: types.Message):
    text = (
        "✨ <b>Добро пожаловать в пространство метафорических карт</b>\n\n"
        "Это безопасное пространство для самопознания и осознанной работы "
        "с вашими мыслями, эмоциями и внутренними процессами.\n\n"
        "Позвольте себе замедлиться и услышать себя."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎴 Получить карту", callback_data="prepare_card")]
    ])

    await message.answer(text, reply_markup=keyboard)
    await message.answer("Меню 👇", reply_markup=main_menu_kb)


# ================== ОТКРЫТИЕ МЕНЮ ==================
@dp.message(lambda m: m.text == "📋 Меню")
async def open_menu(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=menu_kb)


# ================== ПОДГОТОВКА ==================
@dp.callback_query(lambda c: c.data == "prepare_card")
async def prepare_card(callback: types.CallbackQuery):
    text = (
        "🧘‍♀️ <b>Настройка перед получением карты</b>\n\n"
        "Перед тем как получить карту, выполните следующие шаги:\n\n"
        "1️⃣ <b>Удобно сядьте</b> и закройте глаза на несколько секунд.\n"
        "2️⃣ <b>Сделайте</b> несколько глубоких вдохов и выдохов, отпуская напряжение.\n"
        "3️⃣ <b>Позвольте</b> себе на мгновение отойти от внешних забот и сосредоточиться на своих ощущениях здесь и сейчас.\n"
        "4️⃣ <b>Наблюдайте</b> за своими мыслями и эмоциями, не оценивая их, просто отмечайте.\n"
        "5️⃣ <b>Подумайте</b> о том, что в данный момент вызывает у вас наибольший интерес или беспокойство.\n"
        "6️⃣ <b>Сформеруйте</b> на основе этого ваш запрос.\n\n"
        "✨ Эта карта будет вашим инструментом для понимания себя и ваших текущих переживаний.\n"
        "Примите её с открытым умом и доверьтесь своим ощущениям."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Получить карту", callback_data="get_card")]
    ])

    await callback.message.answer(text, reply_markup=keyboard)


# ================== ПОЛУЧЕНИЕ КАРТЫ ==================
@dp.callback_query(lambda c: c.data == "get_card")
async def send_card(callback: types.CallbackQuery, state: FSMContext):
    files = [
        f for f in os.listdir(CARDS_PATH)
        if f.lower().endswith(('.jpg', '.png'))
    ] if os.path.exists(CARDS_PATH) else []

    if not files:
        await callback.message.answer("❌ В папке cards нет изображений.")
        return

    card_name = random.choice(files)
    file_path = os.path.join(CARDS_PATH, card_name)

    await callback.message.answer_photo(types.FSInputFile(file_path))

    await state.update_data(card=card_name)

    reflection = (
        "━━━━━━━━━━━━━━━━━━━\n"
        "✨ <b>Мини-сессия рефлексии</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "💭 Что первое приходит вам на ум, когда вы смотрите на эту карту?\n\n"
        "💡 Какие эмоции или ощущения она у вас вызывает?\n\n"
        "🔍 Как эта карта может помочь вам понять текущую ситуацию или сделать следующий шаг?\n\n"
        "🌟 <i>Совет:</i> Отвечайте честно себе, без самокритики, наблюдайте свои внутренние реакции.\n"
        "🕯 Можно сделать небольшой перерыв, вдохнуть глубоко и записать мысли в блокнот."
    )

    await callback.message.answer(reflection, reply_markup=post_card_kb)


# ================== ХОЧУ НА ИГРУ ==================
@dp.callback_query(lambda c: c.data == "want_game")
async def want_game(callback: types.CallbackQuery):
    user = callback.from_user

    text = (
        f"🎮 <b>Новый запрос на Т-Игру</b>\n\n"
        f"👤 @{user.username or user.id}\n"
        f"ID: {user.id}"
    )

    await bot.send_message(PRACTITIONER_ID, text)

    await callback.message.answer(
        "✅ Ваш запрос отправлен.\n"
        "С вами свяжутся в ближайшее время."
    )


# ================== ЗАДАТЬ ВОПРОС ==================
@dp.callback_query(lambda c: c.data == "ask_question")
async def ask_question(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_question)

    await callback.message.answer(
        "✍️ Напишите ваш вопрос по карте:",
        reply_markup=ForceReply(input_field_placeholder="Введите вопрос...")
    )


# ================== ПРИЁМ ВОПРОСА ==================
@dp.message(UserState.waiting_question)
async def receive_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    card_name = data.get("card")

    user = message.from_user
    question = message.text

    header = (
        f"❓ <b>Вопрос по карте</b>\n\n"
        f"👤 @{user.username or user.id}\n"
        f"ID: {user.id}\n\n"
        f"📝 {question}"
    )

    if card_name:
        file_path = os.path.join(CARDS_PATH, card_name)
        if os.path.exists(file_path):
            await bot.send_photo(
                PRACTITIONER_ID,
                types.FSInputFile(file_path),
                caption=header
            )
        else:
            await bot.send_message(PRACTITIONER_ID, header)
    else:
        await bot.send_message(PRACTITIONER_ID, header)

    reply_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✏ Ответить пользователю",
            callback_data=f"reply_{user.id}"
        )]
    ])

    await bot.send_message(PRACTITIONER_ID, "Ответить:", reply_markup=reply_kb)

    await message.answer("✅ Вопрос отправлен. Ответ придёт сюда.")
    await state.clear()


# ================== ОТВЕТ ПРАКТИКА ==================
@dp.callback_query(lambda c: c.data.startswith("reply_"))
async def reply_user(callback: types.CallbackQuery):
    user_id = int(callback.data.replace("reply_", ""))

    await callback.message.answer(
        f"🖊 Напишите ответ пользователю ({user_id}):",
        reply_markup=ForceReply()
    )


@dp.message(lambda m: m.reply_to_message and "Напишите ответ пользователю" in m.reply_to_message.text)
async def send_answer(message: types.Message):
    user_id = int(
        message.reply_to_message.text.split("(")[1].replace("):", "").replace(")", "")
    )

    answer = (
        "━━━━━━━━━━━━━━━━━━━\n"
        "✨ <b>Ответ игропрактика</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"{message.text}\n\n"
        "───────────────────\n"
        "🌿 Позвольте себе прочувствовать этот ответ.\n"
        "Отметьте, что откликается внутри."
    )

    after_answer_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎴 Получить новую карту", callback_data="prepare_card")],
        [InlineKeyboardButton(text="🎮 Хочу на Т-Игру", callback_data="want_game")],
        [InlineKeyboardButton(text="🔗 Перейти на канал", url=CHANNEL_URL)]
    ])

    await bot.send_message(user_id, answer, reply_markup=after_answer_kb)
    await message.answer("✅ Ответ отправлен.")


# ================== ЗАПУСК ==================
async def main():
    print("Бот запущен 🚀")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())




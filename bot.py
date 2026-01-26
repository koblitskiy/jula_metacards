import asyncio
import os
import random

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ====== НАСТРОЙКИ ======
BOT_TOKEN = os.getenv("BOT_TOKEN")
PRACTITIONER_ID = int(os.getenv("PRACTITIONER_ID"))
CHANNEL_USERNAME = "@your_channel_username"  # без https://

CARDS_FOLDER = "cards"

# ====== FSM ======
class UserState(StatesGroup):
    choosing_area = State()
    waiting_card = State()
    waiting_text = State()

# ====== BOT ======
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ====== КЛАВИАТУРЫ ======
areas_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💼 Работа", callback_data="area_work")],
        [InlineKeyboardButton(text="❤️ Отношения", callback_data="area_love")],
        [InlineKeyboardButton(text="🧠 Здоровье", callback_data="area_health")],
        [InlineKeyboardButton(text="💰 Финансы", callback_data="area_money")],
        [InlineKeyboardButton(text="✈️ Переезд", callback_data="area_move")],
    ]
)

get_card_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🃏 Получить карту", callback_data="get_card")]
    ]
)

# ====== START ======
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет ✨\n\nВыбери жизненную сферу:",
        reply_markup=areas_kb
    )
    await state.set_state(UserState.choosing_area)

# ====== ВЫБОР СФЕРЫ ======
@dp.callback_query(F.data.startswith("area_"))
async def choose_area(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(area=call.data)
    await call.message.answer(
        "Сейчас ты получишь свою метафорическую карту.\n\n"
        "Посмотри на неё и подумай:\n"
        "— что ты в ней видишь?\n"
        "— как она отражает твоё состояние?",
        reply_markup=get_card_kb
    )
    await state.set_state(UserState.waiting_card)

# ====== ВЫДАЧА КАРТЫ ======
@dp.callback_query(F.data == "get_card")
async def send_card(call: CallbackQuery, state: FSMContext):
    await call.answer()

    cards = os.listdir(CARDS_FOLDER)
    card = random.choice(cards)
    card_path = os.path.join(CARDS_FOLDER, card)

    await bot.send_photo(
        chat_id=call.from_user.id,
        photo=open(card_path, "rb"),
        caption="📝 Напиши, что ты видишь на этой карте.\nЯ помогу тебе разобраться."
    )

    await state.update_data(card=card)
    await state.set_state(UserState.waiting_text)

# ====== ТЕКСТ ОТ ПОЛЬЗОВАТЕЛЯ ======
@dp.message(UserState.waiting_text)
async def user_text(message: Message, state: FSMContext):
    data = await state.get_data()

    text_to_practitioner = (
        f"🧑 Клиент: {message.from_user.full_name}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"🃏 Карта: {data.get('card')}\n\n"
        f"💬 Сообщение:\n{message.text}"
    )

    reply_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍ Ответить клиенту",
                    callback_data=f"reply_{message.from_user.id}"
                )
            ]
        ]
    )

    await bot.send_message(
        PRACTITIONER_ID,
        text_to_practitioner,
        reply_markup=reply_kb
    )

    await message.answer("Спасибо ✨ Игропрактик скоро тебе ответит.")
    await state.clear()

# ====== ОТВЕТ ИГРОПРАКТИКА ======
@dp.callback_query(F.data.startswith("reply_"))
async def practitioner_reply(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user_id = int(call.data.split("_")[1])
    await state.update_data(reply_to=user_id)
    await call.message.answer("Напиши ответ клиенту:")

@dp.message(F.from_user.id == PRACTITIONER_ID)
async def send_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_to")

    if not user_id:
        return

    await bot.send_message(user_id, f"💌 Ответ игропрактика:\n\n{message.text}")
    await message.answer("Ответ отправлен ✅")
    await state.clear()

# ====== MAIN ======
async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

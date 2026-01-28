import asyncio
import random
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.filters import Command

TOKEN = "ВСТАВЬ_СЮДА_ТОКЕН_БОТА"
IGROPRACTIC_ID = 123456789  # ← ID игропрактика

CARDS_FOLDER = "cards"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Клавиатуры
start_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Начать")]],
    resize_keyboard=True
)

sphere_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Работа")],
        [KeyboardButton(text="Отношения")],
        [KeyboardButton(text="Здоровье")],
        [KeyboardButton(text="Финансы")],
        [KeyboardButton(text="Переезд")]
    ],
    resize_keyboard=True
)

card_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Получить карту")]],
    resize_keyboard=True
)


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет ✨\nНажми «Начать», чтобы получить метафорическую карту.",
        reply_markup=start_kb
    )


@dp.message(F.text == "Начать")
async def choose_sphere(message: Message):
    await message.answer(
        "Выбери сферу жизни:",
        reply_markup=sphere_kb
    )


@dp.message(F.text.in_(["Работа", "Отношения", "Здоровье", "Финансы", "Переезд"]))
async def send_card_instruction(message: Message):
    await message.answer(
        "Сейчас ты получишь свою метафорическую карту.\n"
        "Посмотри на неё и подумай:\n"
        "— как она отражает твоё текущее состояние?\n"
        "— что ты в ней видишь?",
        reply_markup=card_kb
    )


@dp.message(F.text == "Получить карту")
async def send_card(message: Message):
    cards = os.listdir(CARDS_FOLDER)
    card = random.choice(cards)

    photo_path = os.path.join(CARDS_FOLDER, card)

    await message.answer_photo(
        photo=open(photo_path, "rb"),
        caption="Напиши, что ты видишь на этой карте. Я помогу тебе разобраться ✨"
    )


@dp.message()
async def forward_to_igropractic(message: Message):
    await bot.send_message(
        IGROPRACTIC_ID,
        f"Сообщение от @{message.from_user.username or message.from_user.id}:\n\n{message.text}"
    )
    await message.answer("Спасибо 🙏 Я передал твоё сообщение.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

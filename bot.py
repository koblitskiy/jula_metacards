import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = os.getenv("TELEGRAM_TOKEN")  # добавь токен через Render Dashboard

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Бот работает ✅")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

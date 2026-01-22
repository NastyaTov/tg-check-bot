import os
import smtplib
import asyncio
from email.message import EmailMessage

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ======================
# НАСТРОЙКИ
# ======================
BOT_TOKEN = "8505195706:AAF6tJXKuK879TkUytXgvA4dOPWr3WCZY5Y"

SMTP_EMAIL = "CheckReportSber@gmail.com"
SMTP_PASSWORD = "oisypvcu ksfg aqfz"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

RECIPIENTS = [
    "Avatovkach@sberbank.ru",
    "Mmazhukova@sberbank.ru"
]

# ======================
# ИНИЦИАЛИЗАЦИЯ
# ======================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}

# ======================
# КЛАВИАТУРЫ
# ======================
def keyboard_no_send():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Сбросить")]],
        resize_keyboard=True
    )

def keyboard_with_send():
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text="📨 Отправить"),
            KeyboardButton(text="❌ Сбросить")
        ]],
        resize_keyboard=True
    )

# ======================
# EMAIL
# ======================
def send_email(photos, fio):
    msg = EmailMessage()
    msg["Subject"] = f"Чеки"
    msg["From"] = SMTP_EMAIL
    msg["To"] = ", ".join(RECIPIENTS)
    msg.set_content(f"Отправитель: {fio}")

    for photo in photos:
        with open(photo, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="image",
                subtype="jpeg",
                filename=os.path.basename(photo)
            )

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)

# ======================
# /start
# ======================
@dp.message(Command("start"))
async def start(message: types.Message):
    user_data[message.from_user.id] = {"fio": None, "photos": []}
    await message.answer(
        "👋 Введите ФИО отправителя",
        reply_markup=keyboard_no_send()
    )

# ======================
# ФИО
# ======================
@dp.message(lambda m: m.text and m.text not in ["📨 Отправить", "❌ Сбросить"])
async def set_fio(message: types.Message):
    fio = message.text.strip()

    if len(fio.split()) < 2:
        await message.answer("❌ Введите ФИО полностью")
        return

    user_data[message.from_user.id] = {"fio": fio, "photos": []}
    await message.answer(
        "📸 Теперь отправьте фото чеков",
        reply_markup=keyboard_no_send()
    )

# ======================
# ФОТО
# ======================
@dp.message(lambda m: m.photo)
async def receive_photo(message: types.Message):
    data = user_data.get(message.from_user.id)

    if not data or not data["fio"]:
        await message.answer("❌ Сначала ФИО")
        return

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    path = f"receipt_{message.from_user.id}_{len(data['photos'])+1}.jpg"

    await bot.download_file(file.file_path, path)
    data["photos"].append(path)

    await message.answer("📸 Фото добавлено", reply_markup=keyboard_with_send())

# ======================
# ОТПРАВКА
# ======================
@dp.message(lambda m: m.text == "📨 Отправить")
async def send_photos(message: types.Message):
    data = user_data.get(message.from_user.id)

    if not data or not data["photos"]:
        await message.answer("❌ Нет фото")
        return

    await asyncio.to_thread(send_email, data["photos"], data["fio"])

    for p in data["photos"]:
        os.remove(p)

    user_data[message.from_user.id] = {"fio": None, "photos": []}
    await message.answer("✅ Отправлено", reply_markup=keyboard_no_send())

# ======================
# ЗАПУСК
# ======================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
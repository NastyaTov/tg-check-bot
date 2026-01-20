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
SMTP_PORT = 587

RECIPIENTS = [
    "Avatovkach@sberbank.ru",
    "Mmazhukova@sberbank.ru"
]

# ======================
# ИНИЦИАЛИЗАЦИЯ
# ======================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# user_id -> {"fio": str | None, "photos": list}
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
    msg["Subject"] = f"Чеки от {fio}"
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

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)

# ======================
# /start — АВТО ПРИВЕТСТВИЕ
# ======================
@dp.message(Command("start"))
async def start(message: types.Message):
    user_data[message.from_user.id] = {"fio": None, "photos": []}
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "✍️ Введите ФИО отправителя",
        reply_markup=keyboard_no_send()
    )

# ======================
# ВВОД ФИО
# ======================
@dp.message(lambda m: m.text and m.text not in ["📨 Отправить", "❌ Сбросить"])
async def set_fio(message: types.Message):
    user_id = message.from_user.id
    fio = message.text.strip()

    if len(fio.split()) < 2:
        await message.answer("❌ Введите ФИО полностью")
        return

    user_data[user_id] = {"fio": fio, "photos": []}

    await message.answer(
        f"✅ ФИО сохранено: <b>{fio}</b>\n\n"
        "Теперь отправьте фото чеков\n"
        "Загружайте по одной фотографии",
        parse_mode="HTML",
        reply_markup=keyboard_no_send()
    )

# ======================
# ПОЛУЧЕНИЕ ФОТО
# ======================
@dp.message(lambda m: m.photo)
async def receive_photo(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data or user_data[user_id]["fio"] is None:
        await message.answer("❌ Сначала введите ФИО")
        return

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)

    index = len(user_data[user_id]["photos"]) + 1
    file_path = f"receipt_{user_id}_{index}.jpg"

    await bot.download_file(file.file_path, file_path)
    user_data[user_id]["photos"].append(file_path)

    await message.answer(
        f"📸 Фото №{index} добавлено",
        reply_markup=keyboard_with_send()
    )

# ======================
# 📨 ОТПРАВИТЬ
# ======================
@dp.message(lambda m: m.text == "📨 Отправить")
async def send_photos(message: types.Message):
    user_id = message.from_user.id

    if not user_data.get(user_id) or not user_data[user_id]["photos"]:
        await message.answer("❌ Нет фото для отправки")
        return

    fio = user_data[user_id]["fio"]
    photos = user_data[user_id]["photos"]

    send_email(photos, fio)

    for p in photos:
        os.remove(p)

    user_data[user_id] = {"fio": None, "photos": []}

    await message.answer(
        "✅ Чеки отправлены!\n\n"
        "✍️ Введите новое ФИО",
        reply_markup=keyboard_no_send()
    )

# ======================
# ❌ СБРОС
# ======================
@dp.message(lambda m: m.text == "❌ Сбросить")
async def reset(message: types.Message):
    user_data[message.from_user.id] = {"fio": None, "photos": []}
    await message.answer(
        "🔄 Сброшено\n\n"
        "✍️ Введите ФИО отправителя",
        reply_markup=keyboard_no_send()
    )

# ======================
# ЗАПУСК
# ======================
async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import smtplib
from email.message import EmailMessage
from datetime import datetime

# ======================
# НАСТРОЙКИ
# ======================

BOT_TOKEN = "8505195706:AAF6tJXKuK879TkUytXgvA4dOPWr3WCZY5Y"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "CheckReportSber@gmail.com"
SMTP_PASS = "oisypvcu ksfg aqfz" 
SENDER_EMAIL = SMTP_USER

RECIPIENTS = [
    "Avatovkach@sberbank.ru",
    "Mmazhukova@sberbank.ru"
]

# ======================
# ВСПОМОГАТЕЛЬНОЕ ЛОГИРОВАНИЕ
# ======================

def log(message: str):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# ======================
# ИНИЦИАЛИЗАЦИЯ
# ======================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_data = {}  # user_id -> {"photos": [], "sent": False}

log("🚀 Бот инициализирован")

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
        keyboard=[[KeyboardButton(text="📨 Отправить"), KeyboardButton(text="❌ Сбросить")]],
        resize_keyboard=True
    )

# ======================
# ОТПРАВКА ПИСЬМА
# ======================

def send_email(photos: list[str]):
    log(f"📧 Начинаю формирование письма ({len(photos)} фото)")

    msg = EmailMessage()
    msg["Subject"] = "Чеки"
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECIPIENTS)
    msg.set_content("Отправлены фото чеков.")

    for photo in photos:
        log(f"📎 Прикрепляю файл: {photo}")
        with open(photo, "rb") as f:
            data = f.read()
        msg.add_attachment(
            data,
            maintype="image",
            subtype="jpeg",
            filename=os.path.basename(photo)
        )

    log("🔐 Подключение к SMTP...")
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(SMTP_USER, SMTP_PASS)
        log("✅ SMTP логин успешен")
        smtp.send_message(msg)

    log("✅ Письмо успешно отправлено")

# ======================
# /start
# ======================

@dp.message(Command("start"))
async def start(message: types.Message):
    user_data[message.from_user.id] = {"photos": [], "sent": False}
    log(f"👤 Пользователь {message.from_user.id} нажал /start")

    await message.answer(
        "👋 Привет!\n📸 Отправьте фото чеков по одному.",
        reply_markup=keyboard_no_send()
    )

# ======================
# ПОЛУЧЕНИЕ ФОТО
# ======================

@dp.message(lambda m: m.photo)
async def receive_photo(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {"photos": [], "sent": False}

    index = len(user_data[user_id]["photos"]) + 1
    log(f"📸 Пользователь {user_id} отправил фото №{index}")

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    path = f"receipt_{user_id}_{index}.jpg"

    await bot.download_file(file.file_path, path)
    user_data[user_id]["photos"].append(path)
    user_data[user_id]["sent"] = False

    log(f"💾 Фото сохранено: {path}")

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
    data = user_data.get(user_id)

    log(f"📨 Пользователь {user_id} нажал «Отправить»")

    if not data or not data["photos"]:
        log("❌ Нет фото для отправки")
        await message.answer("❌ Нет фото для отправки")
        return

    if data.get("sent"):
        log("⏳ Попытка повторной отправки")
        await message.answer("⏳ Чеки уже отправлены")
        return

    try:
        log("🚚 Отправляю письмо...")
        await asyncio.to_thread(send_email, data["photos"])
    except Exception as e:
        log(f"❌ Ошибка SMTP: {e}")
        await message.answer(f"❌ Ошибка отправки:\n{e}")
        return

    for p in data["photos"]:
        if os.path.exists(p):
            os.remove(p)
            log(f"🗑 Удалён файл {p}")

    user_data[user_id] = {"photos": [], "sent": True}

    log(f"✅ Отправка завершена для пользователя {user_id}")

    await message.answer(
        "✅ Чеки отправлены!\n📸 Можно отправлять новые фото",
        reply_markup=keyboard_no_send()
    )

# ======================
# ❌ СБРОС
# ======================

@dp.message(lambda m: m.text == "❌ Сбросить")
async def reset(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {"photos": [], "sent": False}
    log(f"🔄 Пользователь {user_id} сбросил данные")

    await message.answer(
        "🔄 Сброшено\n📸 Пожалуйста, отправьте фото чеков",
        reply_markup=keyboard_no_send()
    )

# ======================
# ЗАПУСК
# ======================

if __name__ == "__main__":
    log("🚀 Бот запущен через polling")
    asyncio.run(dp.start_polling(bot))
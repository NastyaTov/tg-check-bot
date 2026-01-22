import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import smtplib
from email.message import EmailMessage

# ======================
# ПОДСТАВЛЕННЫЕ ПЕРЕМЕННЫЕ
# ======================

BOT_TOKEN = "8505195706:AAF6tJXKuK879TkUytXgvA4dOPWr3WCZY5Y"  # <- замени на свой токен от BotFather
SENDER_EMAIL = "CheckReportSber@gmail.com"             # <- твой email в NotiSend
RECIPIENTS = ["Avatovkach@sberbank.ru", "Mmazhukova@sberbank.ru"]

SMTP_HOST = "smtp.msndr.net"
SMTP_PORT = 465
SMTP_USER = "checkreportsber@gmail.com"               # тот же, что SENDER_EMAIL
SMTP_PASS = "2602acd5ea762769b83e63bdc1eac032"                   # <- пароль SMTP из NotiSend

# ======================
# ИНИЦИАЛИЗАЦИЯ
# ======================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_data = {}  # user_id -> {"photos": list}

# ======================
# КЛАВИАТУРЫ
# ======================
def keyboard_no_send():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Сбросить")]], resize_keyboard=True)

def keyboard_with_send():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📨 Отправить"), KeyboardButton(text="❌ Сбросить")]],
        resize_keyboard=True
    )

# ======================
# ФУНКЦИЯ ОТПРАВКИ ПИСЕМ ЧЕРЕЗ NotiSend SMTP
# ======================
def send_email(photos):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Чеки"
        msg["From"] = SENDER_EMAIL
        msg["To"] = ", ".join(RECIPIENTS)
        msg.set_content("Отправлены чеки.")

        for photo in photos:
            with open(photo, "rb") as f:
                data = f.read()
            msg.add_attachment(data, maintype="image", subtype="jpeg", filename=os.path.basename(photo))

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)

        print("✅ Письмо отправлено через NotiSend SMTP!")

    except Exception as e:
        print(f"❌ Ошибка при отправке через SMTP NotiSend: {e}")

# ======================
# /start
# ======================
@dp.message(Command("start"))
async def start(message: types.Message):
    user_data[message.from_user.id] = {"photos": []}
    await message.answer("👋 Привет!\n📸 Пожалуйста, отправьте фото чеков по одному.", reply_markup=keyboard_no_send())

# ======================
# ПОЛУЧЕНИЕ ФОТО
# ======================
@dp.message(lambda m: m.photo)
async def receive_photo(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"photos": []}

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    index = len(user_data[user_id]["photos"]) + 1
    path = f"receipt_{user_id}_{index}.jpg"
    await bot.download_file(file.file_path, path)
    user_data[user_id]["photos"].append(path)

    await message.answer(f"📸 Фото №{index} добавлено", reply_markup=keyboard_with_send())

# ======================
# 📨 ОТПРАВИТЬ
# ======================
@dp.message(lambda m: m.text == "📨 Отправить")
async def send_photos(message: types.Message):
    user_id = message.from_user.id
    data = user_data.get(user_id)
    if not data or not data["photos"]:
        await message.answer("❌ Нет фото для отправки")
        return

    await asyncio.to_thread(send_email, data["photos"])
    for p in data["photos"]:
        if os.path.exists(p):
            os.remove(p)

    user_data[user_id] = {"photos": []}
    await message.answer("✅ Чеки отправлены!\n📸 Можно отправлять новые фото", reply_markup=keyboard_no_send())

# ======================
# ❌ СБРОС
# ======================
@dp.message(lambda m: m.text == "❌ Сбросить")
async def reset(message: types.Message):
    user_data[message.from_user.id] = {"photos": []}
    await message.answer("🔄 Сброшено\n📸 Пожалуйста, отправьте фото чеков", reply_markup=keyboard_no_send())

# ======================
# ЗАПУСК ЧЕРЕЗ POLLING
# ======================
if __name__ == "__main__":
    print("🚀 Бот запущен через polling...")
    asyncio.run(dp.start_polling(bot))
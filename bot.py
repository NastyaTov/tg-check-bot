import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

# ======================
# НАСТРОЙКИ
# ======================

BOT_TOKEN = "8505195706:AAF6tJXKuK879TkUytXgvA4dOPWr3WCZY5Y"
TELEGRAM_CHAT_ID = -5129189080  # <- сюда будут отправляться чеки (замени на свой чат ID)

# ======================
# ЛОГИ
# ======================

def log(msg: str):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

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
    return ReplyKeyboardMarkup([[KeyboardButton("❌ Сбросить")]], resize_keyboard=True)

def keyboard_with_send():
    return ReplyKeyboardMarkup([[KeyboardButton("📨 Отправить"), KeyboardButton("❌ Сбросить")]], resize_keyboard=True)

# ======================
# Функция отправки фото в Telegram
# ======================

async def send_photos_to_telegram(photos: list[str]):
    for photo_path in photos:
        log(f"🚚 Отправка фото {photo_path} в Telegram")
        try:
            await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=open(photo_path, "rb"))
        except Exception as e:
            log(f"❌ Ошибка при отправке {photo_path}: {e}")

# ======================
# /start
# ======================

@dp.message(Command("start"))
async def start(message: types.Message):
    user_data[message.from_user.id] = {"photos": [], "sent": False}
    log(f"👤 Пользователь {message.from_user.id} нажал /start")
    await message.answer("👋 Привет! Отправьте фото чеков по одному.", reply_markup=keyboard_no_send())

# ======================
# Получение фото
# ======================

@dp.message(lambda m: m.photo)
async def receive_photo(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"photos": [], "sent": False}

    index = len(user_data[user_id]["photos"]) + 1
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    path = f"receipt_{user_id}_{index}.jpg"
    await bot.download_file(file.file_path, path)
    user_data[user_id]["photos"].append(path)
    user_data[user_id]["sent"] = False

    log(f"📸 Фото №{index} сохранено: {path}")
    await message.answer(f"📸 Фото №{index} добавлено", reply_markup=keyboard_with_send())

# ======================
# Отправка
# ======================

@dp.message(lambda m: m.text == "📨 Отправить")
async def send_photos_command(message: types.Message):
    user_id = message.from_user.id
    data = user_data.get(user_id)

    if not data or not data["photos"]:
        log("❌ Нет фото для отправки")
        await message.answer("❌ Нет фото для отправки")
        return

    if data.get("sent"):
        log("⏳ Попытка повторной отправки")
        await message.answer("⏳ Чеки уже отправлены")
        return

    log(f"🚚 Отправка {len(data['photos'])} фото в Telegram...")
    await send_photos_to_telegram(data["photos"])

    # удаляем локальные файлы
    for p in data["photos"]:
        if os.path.exists(p):
            os.remove(p)
            log(f"🗑 Удалён файл {p}")

    user_data[user_id] = {"photos": [], "sent": True}
    log(f"✅ Отправка завершена для пользователя {user_id}")
    await message.answer("✅ Чеки отправлены! Можно отправлять новые фото", reply_markup=keyboard_no_send())

# ======================
# Сброс
# ======================

@dp.message(lambda m: m.text == "❌ Сбросить")
async def reset(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {"photos": [], "sent": False}
    log(f"🔄 Пользователь {user_id} сбросил данные")
    await message.answer("🔄 Сброшено. Отправьте фото чеков", reply_markup=keyboard_no_send())

# ======================
# Запуск
# ======================

if __name__ == "__main__":
    log("🚀 Бот запущен через polling")
    asyncio.run(dp.start_polling(bot))

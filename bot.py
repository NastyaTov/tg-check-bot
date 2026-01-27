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
TELEGRAM_CHAT_ID = -5129189080  # chat_id группы (бот должен быть админом)

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
# Отправка фото в группу
# ======================

async def send_photos_to_telegram(photos: list[str], user: types.User):
    caption_base = (
        "🧾 Новый чек\n"
        f"👤 От: {user.full_name} (@{user.username or 'без username'})\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    for i, photo_path in enumerate(photos, start=1):
        log(f"🚚 Отправка {photo_path} в группу")
        try:
            await bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=types.FSInputFile(photo_path),
                caption=f"{caption_base}\n📎 Фото {i}/{len(photos)}"
            )
            log(f"✅ Фото {photo_path} отправлено")
        except Exception as e:
            log(f"❌ Ошибка при отправке {photo_path}: {e}")

# ======================
# /start
# ======================

@dp.message(Command(commands=["start"]))
async def start(message: types.Message):
    user_data[message.from_user.id] = {"photos": [], "sent": False}
    log(f"👤 Пользователь {message.from_user.id} нажал /start")
    await message.answer(
        "👋 Привет! Загрузите чеки отдельными фотографиями.\n"
        "Когда закончите — нажмите «Отправить».",
        reply_markup=keyboard_no_send()
    )

# ======================
# Получение фото
# ======================

@dp.message(lambda message: message.content_type == "photo")
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
    await message.answer(
        f"📸 Фото №{index} добавлено",
        reply_markup=keyboard_with_send()
    )

# ======================
# Отправка чеков
# ======================

@dp.message(lambda message: message.text == "📨 Отправить")
async def send_photos_command(message: types.Message):
    user_id = message.from_user.id
    data = user_data.get(user_id)

    if not data or not data["photos"]:
        log("❌ Нет фото для отправки")
        await message.answer("❌ Нет фото для отправки")
        return

    if data.get("sent"):
        log("⏳ Повторная отправка запрещена")
        await message.answer("⏳ Чеки уже отправлены")
        return

    log(f"🚚 Отправка {len(data['photos'])} фото в группу")
    await send_photos_to_telegram(data["photos"], message.from_user)

    # удаляем локальные файлы
    for p in data["photos"]:
        if os.path.exists(p):
            os.remove(p)
            log(f"🗑 Удалён файл {p}")

    user_data[user_id] = {"photos": [], "sent": True}
    log(f"✅ Отправка завершена для пользователя {user_id}")

    await message.answer(
        "✅ Чеки отправлены! Можно загружать новые фото.",
        reply_markup=keyboard_no_send()
    )

# ======================
# Сброс
# ======================

@dp.message(lambda message: message.text == "❌ Сбросить")
async def reset(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {"photos": [], "sent": False}
    log(f"🔄 Пользователь {user_id} сбросил данные")
    await message.answer(
        "🔄 Сброшено. Отправьте фото чеков.",
        reply_markup=keyboard_no_send()
    )

# ======================
# Запуск бота
# ======================

if __name__ == "__main__":
    log("🚀 Бот запущен (polling)")
    asyncio.run(dp.start_polling(bot))
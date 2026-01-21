import os
import smtplib
from email.message import EmailMessage
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route

# ======================
# НАСТРОЙКИ
# ======================
BOT_TOKEN = os.getenv("8505195706:AAF6tJXKuK879TkUytXgvA4dOPWr3WCZY5Y")  # Ваш токен бота
SMTP_EMAIL = os.getenv("CheckReportSber@gmail.com")  # Gmail
SMTP_PASSWORD = os.getenv("oisypvcu ksfg aqfz")  # App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # SSL порт

RECIPIENTS = [
    "Avatovkach@sberbank.ru",
    "Mmazhukova@sberbank.ru"
]

# ======================
# ИНИЦИАЛИЗАЦИЯ
# ======================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}  # user_id -> {"fio": str, "photos": list}

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
        keyboard=[[KeyboardButton(text="📨 Отправить"),
                   KeyboardButton(text="❌ Сбросить")]],
        resize_keyboard=True
    )

# ======================
# EMAIL
# ======================
def send_email(photos, fio):
    """
    Синхронная отправка письма через SMTP_SSL
    """
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Чеки от {fio}"
        msg["From"] = SMTP_EMAIL
        msg["To"] = ", ".join(RECIPIENTS)
        msg.set_content(f"Отправитель: {fio}")

        for photo in photos:
            if not os.path.exists(photo):
                print(f"❌ Файл не найден: {photo}")
                continue
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

        print("✅ Письмо успешно отправлено!")

    except smtplib.SMTPAuthenticationError:
        print("❌ Ошибка аутентификации: проверь App Password Gmail")
    except smtplib.SMTPConnectError:
        print("❌ Не удалось подключиться к серверу SMTP")
    except Exception as e:
        print(f"❌ Другая ошибка при отправке email: {e}")

# ======================
# /start
# ======================
@dp.message(Command("start"))
async def start(message: types.Message):
    user_data[message.from_user.id] = {"fio": None, "photos": []}
    await message.answer(
        "👋 Добро пожаловать!\n\n✍️ Введите ФИО отправителя",
        reply_markup=keyboard_no_send()
    )

# ======================
# Ввод ФИО
# ======================
@dp.message(lambda m: m.text and m.text not in ["📨 Отправить", "❌ Сбросить"])
async def set_fio(message: types.Message):
    fio = message.text.strip()
    if len(fio.split()) < 2:
        await message.answer("❌ Введите ФИО полностью")
        return

    user_data[message.from_user.id] = {"fio": fio, "photos": []}
    await message.answer(
        f"✅ ФИО сохранено: <b>{fio}</b>\n\n📸 Теперь отправьте фото чеков",
        parse_mode="HTML",
        reply_markup=keyboard_no_send()
    )

# ======================
# Получение фото
# ======================
@dp.message(lambda m: m.photo)
async def receive_photo(message: types.Message):
    user_id = message.from_user.id
    data = user_data.get(user_id)

    if not data or not data["fio"]:
        await message.answer("❌ Сначала введите ФИО")
        return

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    index = len(data["photos"]) + 1
    path = f"receipt_{user_id}_{index}.jpg"

    await bot.download_file(file.file_path, path)
    data["photos"].append(path)

    await message.answer(
        f"📸 Фото №{index} добавлено",
        reply_markup=keyboard_with_send()
    )

# ======================
# Отправка фото
# ======================
@dp.message(lambda m: m.text == "📨 Отправить")
async def send_photos(message: types.Message):
    user_id = message.from_user.id
    data = user_data.get(user_id)

    if not data or not data["photos"]:
        await message.answer("❌ Нет фото для отправки")
        return

    # Вызов синхронной функции в отдельном потоке, чтобы не блокировать бота
    await asyncio.to_thread(send_email, data["photos"], data["fio"])

    # Удаляем локальные файлы
    for p in data["photos"]:
        if os.path.exists(p):
            os.remove(p)

    user_data[user_id] = {"fio": None, "photos": []}

    await message.answer(
        "✅ Чеки отправлены!\n\n✍️ Введите новое ФИО",
        reply_markup=keyboard_no_send()
    )

# ======================
# Сброс
# ======================
@dp.message(lambda m: m.text == "❌ Сбросить")
async def reset(message: types.Message):
    user_data[message.from_user.id] = {"fio": None, "photos": []}
    await message.answer(
        "🔄 Сброшено\n\n✍️ Введите ФИО отправителя",
        reply_markup=keyboard_no_send()
    )

# ======================
# WEBHOOK + HTTP (Starlette)
# ======================
async def telegram_webhook(request: Request):
    update = types.Update(**await request.json())
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})

async def health(request: Request):
    return JSONResponse({"status": "ok"})

app = Starlette(
    routes=[
        Route("/webhook", telegram_webhook, methods=["POST"]),
        Route("/health", health),
    ]
)

# ======================
# ЗАПУСК
# ======================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
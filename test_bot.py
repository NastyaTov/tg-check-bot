from aiogram import Bot

BOT_TOKEN = "8505195706:AAF6tJXKuK879TkUytXgvA4dOPWr3WCZY5Y"

print("BOT_TOKEN =", type(BOT_TOKEN), BOT_TOKEN)

bot = Bot(token=BOT_TOKEN)
print("Bot created successfully!")
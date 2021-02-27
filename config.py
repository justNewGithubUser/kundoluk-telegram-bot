import os
from aiogram import Bot, Dispatcher, executor, types

# for local development
TOKEN = "1645019435:AAGjQzqiGREh91Ntej3MweRy7ZVSqcsOxcM"
kundoluk_login = "205719304"
kundoluk_password = "1843"

# for heroku
# TOKEN = os.getenv("TOKEN")
# kundoluk_login = os.getenv("LOGIN")
# kundoluk_password = os.getenv("PASSWORD")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

database_path = "database.db"
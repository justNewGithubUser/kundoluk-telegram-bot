import os
from aiogram import Bot, Dispatcher, executor, types

# for local development
# TOKEN = "your token"
# kundoluk_login = "your login"
# kundoluk_password = "your password"

# for heroku
TOKEN = os.getenv("TOKEN")
kundoluk_login = os.getenv("LOGIN")
kundoluk_password = os.getenv("PASSWORD")

bot = Bot(token=TOKEN, parse_mode="html")
dp = Dispatcher(bot)

database_path = "database.db"

# default profile photo file id
default_profile_photo = "AgACAgIAAxkBAAEJPhJgO6QqH7fg1Km7DGSgzz540Y1oFwACO7I" \
                        "xG4584UkSUoYuvjxxGF46CZ4uAAMBAAMCAANtAAOFmQACHgQ"

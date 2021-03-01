import os
from aiogram import Bot, Dispatcher, executor, types

# for local development
# TOKEN = "1561460809:AAErXbVX-EAxZKlks_S26hnUiBnUl1b5wOk"
# kundoluk_login = "205719304"
# kundoluk_password = "1843"

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

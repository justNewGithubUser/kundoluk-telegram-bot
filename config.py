import os

database_path = "database.db"

# for local development
# TOKEN: str = "1561460809:AAErXbVX-EAxZKlks_S26hnUiBnUl1b5wOk"
# kundoluk_login: str = "205719304"
# kundoluk_password: str = "1843"
# default_profile_photo: (str, type(None)) = None  # you can use default profile photo file id
# bot_username = "abrakadabramybottestbot"

# sending reports of bot usage to this telegram user id
reports_user_id: int = 896678539  # replace by your tg user id instead None

# for heroku
TOKEN = os.getenv("TOKEN")
kundoluk_login = os.getenv("LOGIN")
kundoluk_password = os.getenv("PASSWORD")
default_profile_photo = os.getenv("DEF_PROF_PHOTO")
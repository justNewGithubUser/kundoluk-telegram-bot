import os

database_path = "database.db"

# for local development
# TOKEN: str = "your token"
# kundoluk_login: str = "your kundoluk login"
# kundoluk_password: str = "your kundoluk password"
# default_profile_photo: (str, type(None)) = None  # you can use default profile photo file id

# sending reports of bot usage to this telegram user id
reports_user_id: int = 896678539  # replace by your tg user id instead None

# for heroku
TOKEN = os.getenv("TOKEN")
kundoluk_login = os.getenv("LOGIN")
kundoluk_password = os.getenv("PASSWORD")
default_profile_photo = os.getenv("DEF_PROF_PHOTO")
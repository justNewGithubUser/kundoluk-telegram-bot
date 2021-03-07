import os

database_path = "database.db"

# for local development
# TOKEN: str = "bot-token"
# kundoluk_login: str = "your login"
# kundoluk_password: str = "your password"

# sending reports of bot usage to this telegram user id
reports_user_id: int = 896678539  # replace by your tg user id instead None

# for heroku
TOKEN = os.getenv("TOKEN")
kundoluk_login = os.getenv("LOGIN")
kundoluk_password = os.getenv("PASSWORD")
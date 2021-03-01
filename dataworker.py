import sqlite3
from config import database_path

__all__ = "DataWorker", "MediaWorker"


class MediaWorker:

    @staticmethod
    def default_profile_photo():
        return open("media/default_profile_photo.png", "rb")


class DataWorker:

    def __init__(self):
        self.__connection = sqlite3.connect(database_path)
        self.__cursor = self.__connection.cursor()

    def get_pupils_info_all(self, filter_none_users: bool = False,
                            class_id: str = None,
                            pagination_id: (str, int) = None) -> list:
        """Getting all info about all pupils.

        Keyword arguments:
        filter_none_users -- return only that pupils info which 'kundoluk_id' is not equal None

        Order of return values:
        (pupil_id, first_name, last_name, kundoluk_id, class_id, pagination_id)

        """
        query = "SELECT * FROM 'pupils'"
        if any((filter_none_users, class_id, pagination_id)):
            query += " WHERE"
            if class_id:
                if "=" in query:
                    query += " AND"
                query += f" class_id='{class_id}'"
            if pagination_id:
                if "=" in query:
                    query += " AND"
                query += f" pagination_id={pagination_id}"
            if filter_none_users:
                if "=" in query:
                    query += " AND"
                query += " kundoluk_id NOT NULL"
        return self.__cursor.execute(query).fetchall()

    def get_pupil_info(self, pupil_id: (str, int)) -> tuple:
        """Getting all info about pupil.

        Order of return values:
        (pupil_id, first_name, last_name, kundoluk_id, class_id, pagination_id)

        """
        query = f"SELECT * FROM 'pupils' WHERE pupil_id={pupil_id}"
        return self.__cursor.execute(query).fetchone()

    def get_lesson_info(self, lesson_id: (str, int)) -> tuple:
        """Getting info about lesson.

        Order of return values:
        (lesson_id, lesson_name, lesson_kundoluk_id, emoji_shortcode, pagination_id)

        """
        query = f"SELECT * FROM 'lessons' WHERE lesson_id='{lesson_id}';"
        return self.__cursor.execute(query).fetchone()

    def lessons_info(self, pagination_id: (int, str) = None) -> list:
        """Getting all info about lessons.

        Order of return values:
        (lesson_id, lesson_name, lesson_kundoluk_id, emoji_shortcode, pagination_id)

        """
        query = "SELECT * FROM 'lessons'"
        if pagination_id is not None:
            query += f" WHERE pagination_id={pagination_id};"
        return self.__cursor.execute(query).fetchall()

    @property
    def classes_info(self) -> list:
        """Getting all classes list."""
        query = "SELECT * FROM classes;"
        return self.__cursor.execute(query).fetchall()

    def get_class_name(self, class_id: str) -> str:
        """Getting class_name by class_id."""
        query = f"SELECT class_name FROM classes WHERE class_id='{class_id}'"
        return self.__cursor.execute(query).fetchone()[0]

    def get_lesson_name(self, lesson_id: (str, int)) -> str:
        """Getting lesson_name by lesson_id."""
        query = f"SELECT lesson_name FROM lessons WHERE lesson_id='{lesson_id}'"
        return self.__cursor.execute(query).fetchone()[0]

    def __del__(self):
        self.__connection.close()
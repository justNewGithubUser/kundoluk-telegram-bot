import sqlite3
from config import database_path

__all__ = "Dataworker"


class Dataworker:

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
        (pupil_id, first_name, last_name, kundoluk_id, class_id)

        """
        query = "SELECT * FROM 'pupils'"
        if filter_none_users and class_id:
            query += f" WHERE kundoluk_id NOT NULL AND class_id='{class_id}';"
        else:
            if filter_none_users:
                query += " WHERE kundoluk_id NOT NULL;"
            elif class_id:
                query += f" WHERE class_id='{class_id}'"
        return self.__cursor.execute(query).fetchall()

    def get_pupil_info(self, pupil_id: (str, int)) -> tuple:
        """Getting all info about pupil.

        Order of return values:
        (pupil_id, first_name, last_name, kundoluk_id, class_id)

        """
        query = f"SELECT * FROM 'pupils' WHERE pupil_id={pupil_id}"
        return self.__cursor.execute(query).fetchone()

    def get_lesson_info(self, lesson_id: (str, int)) -> tuple:
        """Getting info about lesson.

        Order of return values:
        (lesson_id, lesson_name, lesson_kundoluk_id, emoji_shortcode)

        """
        query = f"SELECT * FROM 'lessons' WHERE lesson_id='{lesson_id}';"
        return self.__cursor.execute(query).fetchone()

    @property
    def lessons_info(self) -> list:
        """Getting all info about lessons.

        Order of return values:
        (lesson_id, lesson_name, lesson_kundoluk_id, emoji_shortcode)

        """
        query = "SELECT * FROM 'lessons';"
        return self.__cursor.execute(query).fetchall()

    @property
    def classes_info(self) -> list:
        """Getting all classes list."""
        query = "SELECT * FROM classes;"
        return self.__cursor.execute(query).fetchall()

    def __del__(self):
        self.__connection.close()


if __name__ == '__main__':
    from pprint import pprint
    db = Dataworker()
    # pprint(db.get_pupils_info_all())
    pprint(db.get_lesson_info(2))
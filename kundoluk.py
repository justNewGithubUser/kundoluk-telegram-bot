import asyncio
from pprint import pprint
from time import time
import aiohttp
import bs4
from dataworker import Dataworker
from config import kundoluk_login, kundoluk_password
from utils import format_maps


class Diary:
    __login_url = "https://kundoluk.edu.kg/account/login"
    __marks_journal_url = "https://kundoluk.edu.kg/journal/student"

    def __init__(self):
        self.__login_data = {"login": kundoluk_login, "password": kundoluk_password}
        self.__tasks = []

    async def __request_to_lesson_page(self, session: aiohttp.ClientSession,
                                       user_kundoluk_id: (str, int),
                                       lesson_kundoluk_id: (str, int),
                                       quarter: (int, str) = 0):
        """"""
        url_to_request = f"{self.__marks_journal_url}/{user_kundoluk_id}/{lesson_kundoluk_id}?quarter={quarter}"
        async with session.get(url_to_request) as response:
            return await response.text()

    async def get_lesson_responses(self, user_id: (int, str), *args):
        async with aiohttp.ClientSession() as session:
            async with session.post(url=self.__login_url, data=self.__login_data):
                db = Dataworker()
                user_kundoluk_id = db.get_pupil_info(user_id)[3]
                if not args:
                    args = [info[0] for info in db.lessons_info]
                for lesson_id in args:
                    lesson_kundoluk_id = db.get_lesson_info(lesson_id)[2]
                    task = asyncio.create_task(self.    __request_to_lesson_page(session,
                                                                             user_kundoluk_id,
                                                                             lesson_kundoluk_id))
                    self.__tasks.append(task)
                responses = await asyncio.gather(*self.__tasks)
        await session.close()
        self.__tasks.clear()
        return [r.translate(format_maps["middle"]) for r in responses]


async def main():
    db = Dataworker()
    diary = Diary()
    lesson_ids = [i[0] for i in db.lessons_info]
    s = await diary.get_lesson_responses(44, *lesson_ids)
    for i in s:
        print(type(i))


if __name__ == '__main__':
    start = time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print(time() - start)

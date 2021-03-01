import asyncio
from pprint import pprint
from time import time
import aiohttp
import bs4
from aiogram.types import InputMediaPhoto
from dataworker import DataWorker
from config import kundoluk_login, kundoluk_password
from utils import format_maps

db = DataWorker()


class Kundoluk:
    __login_url = "https://kundoluk.edu.kg/account/login"
    __marks_journal_url = "https://kundoluk.edu.kg/journal/student"
    __profile_photo_url = "https://kundoluk.edu.kg/media/users/{}/photo_preview.jpg"

    def __init__(self):
        self.__login_data = {"login": kundoluk_login, "password": kundoluk_password}
        self.__tasks = []
        self.__marks_html = None
        self.average_mark = None

    def get_profile_photo_url(self, pupil_id: (str, int)):
        pupil_kundoluk_id = db.get_pupil_info(pupil_id)[3]
        return self.__profile_photo_url.format(pupil_kundoluk_id)

    async def __request_to_pupil_diary(self, pupil_id: (str, int),
                                       lesson_id: (str,int),
                                       quarter: (str, int) = 0):
        async with aiohttp.ClientSession() as session:
            async with session.post(self.__login_url, data=self.__login_data):
                _, _, _, kundoluk_id, _, _ = db.get_pupil_info(pupil_id)
                _, _, lesson_kundoluk_id, _, _ = db.get_lesson_info(lesson_id)
                marks_journal_url = f"{self.__marks_journal_url}/{kundoluk_id}/{lesson_kundoluk_id}?quarter={quarter}"
                async with session.get(marks_journal_url) as response:
                    return await response.text()

    async def get_pupil_marks(self, pupil_id: (str, int), lesson_id: (str, int), filter_empty_marks=True):
        self.__marks_html = await self.__request_to_pupil_diary(pupil_id, lesson_id)
        soup = bs4.BeautifulSoup(self.__marks_html, "lxml")
        self.average_mark = soup.find("div", class_="average").find("span").text
        table_rows = soup.find("tbody").find_all("tr")
        buffer = []
        for tr in table_rows:
            mark_date = tr.find_all("td")[1].text
            mark_value = tr.find_all("td")[3].text.translate(format_maps["full"])
            if filter_empty_marks and not mark_value:
                continue
            buffer.append((mark_date, mark_value))
        return buffer

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
                user_kundoluk_id = db.get_pupil_info(user_id)[3]
                if not args:
                    args = [info[0] for info in db.lessons_info()]
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
    kundoluk = Kundoluk()
    a = await kundoluk.get_pupil_marks(3, 4)
    print(a)

if __name__ == '__main__':
    start = time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print(time() - start)
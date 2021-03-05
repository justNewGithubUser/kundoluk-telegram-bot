import asyncio
import aiohttp
import bs4
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

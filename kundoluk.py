import asyncio
from pprint import pprint
from time import time
import aiohttp
from bs4 import BeautifulSoup
from dataworker import Dataworker


class Kundoluk:
    __login_url = "https://kundoluk.edu.kg/account/login"
    __marks_journal_url = "https://kundoluk.edu.kg/journal/student"

    def __init__(self, login_data: dict):
        self.__login_data = login_data
        self.__tasks = []


class Diary(Kundoluk):

    def __init__(self, login_data: dict):
        super().__init__(login_data)

    async def __get_pupil_progress_info(self, session: aiohttp.ClientSession,
                                        user_kundoluk_id: (str, int),
                                        lesson_kundoluk_id: (str, int),
                                        quarter: (int, str) = 0) -> aiohttp.client.ClientResponse:
        url_to_request = f"{self.__marks_journal_url}/{user_kundoluk_id}/{lesson_kundoluk_id}?quarter={quarter}"
        async with session.get(url_to_request) as response:
            return response

    async def analyze_pupil_progress(self, user_id: (int, str), *args):
        session = aiohttp.ClientSession()
        async with session.post(url=self.__login_url, data=self.__login_data):
            db = Dataworker()
            user_kundoluk_id = db.get_pupil_info(user_id)[3]
            if not args:
                args = [info[0] for info in db.lessons_info]
            for lesson_id in args:
                lesson_kundoluk_id = db.get_lesson_info(lesson_id)[2]
                task = asyncio.create_task(self.__get_pupil_progress_info(session,
                                                                          user_kundoluk_id,
                                                                          lesson_kundoluk_id))
                self.__tasks.append(task)
            responses = await asyncio.gather(*self.__tasks)
        await session.close()
        self.__tasks.clear()
        return responses

async def main():
    user = Kundoluk({"login": "205719304", "password": "1843"})
    db = Dataworker()
    r = await user.analyze_pupil_progress(78, )
    print(r)

if __name__ == '__main__':
    start = time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print(time()-start)
from random import choice
from emoji import emojize
from aiogram import types, Dispatcher, Bot, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.utils.exceptions import WrongFileIdentifier, InvalidHTTPUrlContent
from config import default_profile_photo, TOKEN
from dataworker import *
from kundoluk import Kundoluk
from utils import callback_queries, check_caller_telegram_id

bot = Bot(token=TOKEN, parse_mode="html")
dp = Dispatcher(bot)

db = DataWorker()
kundoluk = Kundoluk()


@dp.callback_query_handler(lambda call: call.data.startswith("show_classes"))
@check_caller_telegram_id
async def process_show_classes_callback(call: types.CallbackQuery):
    caller_tg_id = call.data.split("?")[1:][0]
    caller_first_name = call.from_user.first_name
    caller_last_name = call.from_user.last_name
    if caller_last_name:
        answer_template = f"{caller_first_name} {caller_last_name}, выберите пожалуйста класс."
    else:
        answer_template = f"{caller_first_name}, выберите пожалуйста класс."

    markup = InlineKeyboardMarkup()
    classes_btns = [
        InlineKeyboardButton(
            text=f"{emojize(cls_emoji, use_aliases=True)} {cls_name}",
            callback_data=callback_queries["parse_class"].format(
                caller_tg_id=caller_tg_id,
                cls_id=cls_id,
                cls_name=cls_name,
                pagination_id=1,
                reload=0))
        for cls_id, cls_name, cls_emoji in db.classes_info
    ]
    markup.add(*classes_btns)

    await bot.edit_message_text(answer_template, call.message.chat.id,
                                call.message.message_id, reply_markup=markup)


@dp.callback_query_handler(lambda call: call.data.startswith("parse_class"))
@check_caller_telegram_id
async def process_parse_class_callback(call: types.CallbackQuery):
    caller_telegram_id, class_id, class_name, pagination_id, reload = call.data.split("?")[1:]
    await call.answer("")
    markup = InlineKeyboardMarkup(row_width=2)
    pupils_info = db.get_pupils_info_all(filter_none_users=True, class_id=class_id, pagination_id=pagination_id)

    for pupil_id, first_name, last_name, kundoluk_id, class_id, pagination_id in pupils_info:
        i = choice(("\u25AA\uFE0F", "\u25AB\uFE0F"))
        btn_text = f"{i} {last_name[0]}. {first_name}"
        btn_callback_data = f"parse_pupil?{caller_telegram_id}?{pupil_id}?{pagination_id}?1"
        btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
        markup.insert(btn)
    else:
        if pagination_id != 2:
            if pagination_id == 1:
                btn_text = "След. страница »"
            elif pagination_id == 3:
                btn_text = "« Пред. страница"
            btn_callback_data = f"parse_class?{caller_telegram_id}?{class_id}?{class_name}?2?0"
            btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
            markup.add(btn)
        else:
            btns = []
            for i, text in ((1, "« Пред. страница"), (3, "След. страница »")):
                btn_callback_data = f"parse_class?{caller_telegram_id}?{class_id}?{class_name}?{i}?0"
                btn = InlineKeyboardButton(text=text, callback_data=btn_callback_data)
                btns.append(btn)
            markup.add(*btns)
        markup.add(InlineKeyboardButton(text="«« Назад", callback_data=f"show_classes?{caller_telegram_id}"))
        if not int(reload):
            await call.message.edit_text(f"Класс {class_name}", reply_markup=markup)
        else:
            await call.message.delete()
            await call.message.answer(f"Класс {class_name}", reply_markup=markup)


@dp.callback_query_handler(lambda call: call.data.startswith("parse_pupil"))
@check_caller_telegram_id
async def process_parse_pupil_callback(call: types.CallbackQuery):
    caller_tg_id, pupil_id, current_pag_id, reload = call.data.split("?")[1:]
    await call.answer(text="")

    _, first_name, last_name, _, class_id, _ = db.get_pupil_info(pupil_id)
    class_name = db.get_class_name(class_id)
    caption_template = f"<b>{last_name} {first_name}</b>, {class_name}"

    markup = InlineKeyboardMarkup(row_width=2)

    btn_text = "Оценки"
    btn_callback_data = f"parse_marks?{caller_tg_id}?{pupil_id}?1"
    marks_btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)

    btn_text = "Анализ"
    btn_callback_data = f"analyze_marks?{pupil_id}?{caller_tg_id}?"
    analyze_btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)

    btn_text = "«« Назад"
    btn_callback_data = f"parse_class?{caller_tg_id}?{class_id}?{class_name}?{current_pag_id}?1"
    back_btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)

    markup.add(marks_btn, analyze_btn, back_btn)
    if int(reload):
        profile_photo_url = kundoluk.get_profile_photo_url(pupil_id)
        await call.message.delete()
        try:
            await call.message.answer_photo(photo=profile_photo_url, caption=caption_template, reply_markup=markup)
        except (WrongFileIdentifier, InvalidHTTPUrlContent):
            if default_profile_photo is None:
                with open("media/default_profile_photo.png", "rb") as photo:
                    await call.message.answer_photo(photo, caption_template, reply_markup=markup)
            else:
                await call.message.answer_photo(default_profile_photo, caption_template, reply_markup=markup)
    else:
        await call.message.edit_reply_markup(markup)


@dp.callback_query_handler(lambda call: call.data.startswith("parse_marks"))
@check_caller_telegram_id
async def process_parse_marks_callback(call: types.CallbackQuery):
    caller_tg_id, pupil_id, pagination_id = call.data.split("?")[1:]
    markup = InlineKeyboardMarkup(row_width=2)
    for lesson_id, lesson_name, _, emoji_shortcode, _ in db.lessons_info(pagination_id):
        btn_text = f"{emojize(emoji_shortcode, use_aliases=True)} {lesson_name}"
        btn_callback_data = f"parse_lesson_marks?{caller_tg_id}?{pupil_id}?{lesson_id}?{pagination_id}"
        btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
        markup.insert(btn)
    else:
        if pagination_id == "1":
            btn_text = "След.страница »"
            btn_callback_data = f"parse_marks?{caller_tg_id}?{pupil_id}?2"
        elif pagination_id == "2":
            btn_text = "« Пред.страница"
            btn_callback_data = f"parse_marks?{caller_tg_id}?{pupil_id}?1"
        page_btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
        btn_text = "«« Назад"
        btn_callback_data = f"parse_pupil?{caller_tg_id}?{pupil_id}?{pagination_id}?0"
        back_btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
        markup.add(back_btn, page_btn)

    await call.message.edit_reply_markup(markup)


@dp.callback_query_handler(lambda call: call.data.startswith("parse_lesson_marks"))
@check_caller_telegram_id
async def process_parse_lesson_marks_callback(call: types.CallbackQuery):
    caller_tg_id, pupil_id, lesson_id, pagination_id = call.data.split("?")[1:]
    _, first_name, last_name, _, class_id, _ = db.get_pupil_info(pupil_id)
    class_name = db.get_class_name(class_id)
    lesson_name = db.get_lesson_name(lesson_id)
    marks = await kundoluk.get_pupil_marks(pupil_id, lesson_id)
    average_mark = kundoluk.average_mark
    edit_text_template = f"<b>{last_name} {first_name}</b>, {class_name}\n<b>{lesson_name}</b>\n"
    split_line = "-" * len(edit_text_template)
    edit_text_template += split_line

    for mark_date, mark_value in marks:
        edit_text_template += f"\n{mark_date} - {mark_value}"
    else:
        edit_text_template += f"\n{split_line}\nСредняя оценка - {average_mark}"

    markup = InlineKeyboardMarkup(row_width=1)
    btn_text = "«« Назад"
    btn_callback_data = f"parse_marks?{caller_tg_id}?{pupil_id}?{pagination_id}"
    back_btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
    markup.add(back_btn)

    await call.message.edit_caption(edit_text_template, reply_markup=markup)


@dp.callback_query_handler(lambda call: call.data.startswith("analyze_marks"))
@check_caller_telegram_id
async def process_analyze_marks_callback(call: types.CallbackQuery):
    await call.answer("Раздел в доработке :)", show_alert=True)


@dp.message_handler(commands=["marks"])
async def process_marks_command(message: types.Message):
    caller_telegram_id = message.from_user.id
    caller_first_name = message.from_user.first_name
    caller_last_name = message.from_user.last_name
    if caller_last_name:
        answer_template = f"{caller_first_name} {caller_last_name}, выберите пожалуйста класс."
    else:
        answer_template = f"{caller_first_name}, выберите пожалуйста класс."

    markup = InlineKeyboardMarkup(row_width=3)
    for cls_id, cls_name, cls_emoji in db.classes_info:
        btn_text = f"{emojize(cls_emoji, use_aliases=True)} {cls_name}"
        btn_callback_data = f"parse_class?{caller_telegram_id}?{cls_id}?{cls_name}?1?0"
        btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
        markup.insert(btn)

    await bot.send_message(896678539, f"{caller_first_name}, {message.from_user.username}, {caller_telegram_id}")
    await message.answer(text=answer_template, reply_markup=markup)


@dp.message_handler(lambda message: message.chat.type == "private")
async def process_all_messages(message: types.Message):
    await message.answer("/marks - посмотреть оценки")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

from random import choice

from aiogram import types, Dispatcher, Bot, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.emoji import emojize
from aiogram.dispatcher.filters import Command, Text
from aiogram.utils.exceptions import WrongFileIdentifier, InvalidHTTPUrlContent, \
    MessageNotModified, MessageToDeleteNotFound

from utils import callback_queries, check_caller_telegram_id
from config import default_profile_photo, TOKEN, reports_user_id
from kundoluk import Kundoluk
from dataworker import *

bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

db = DataWorker()
kundoluk = Kundoluk()


@dp.callback_query_handler(Text(startswith="show_classes"))
@check_caller_telegram_id
async def process_show_classes_callback(call: types.CallbackQuery):
    caller_tg_id = call.data.split("?")[1:][0]
    caller_first_name = call.from_user.first_name
    caller_last_name = call.from_user.last_name

    answer_template = f"{caller_first_name}{' ' + caller_last_name if caller_last_name else ''}, выберите класс."

    markup = InlineKeyboardMarkup()
    classes_btns = [
        InlineKeyboardButton(
            text=f"{emojize(cls_emoji)} {cls_name}",
            callback_data=callback_queries["parse_class"].format(
                caller_tg_id=caller_tg_id,
                cls_id=cls_id,
                cls_name=cls_name,
                pagination_id=1,
                reload=0)
        )
        for cls_id, cls_name, cls_emoji in db.classes_info
    ]
    markup.add(*classes_btns)

    try:
        await bot.edit_message_text(answer_template, call.message.chat.id,
                                    call.message.message_id, reply_markup=markup)
    except MessageNotModified:
        await call.answer("Ожидайте...")


@dp.callback_query_handler(Text(startswith="parse_class"))
@check_caller_telegram_id
async def process_parse_class_callback(call: types.CallbackQuery):
    await call.answer("")

    caller_telegram_id, class_id, class_name, pagination_id, reload = call.data.split("?")[1:]
    markup = InlineKeyboardMarkup(row_width=2)
    pupils_info = db.get_pupils_info_all(filter_none_users=True, class_id=class_id, pagination_id=pagination_id)

    btns = [
        InlineKeyboardButton(
            text=f"{last_name[0]}. {first_name}",
            callback_data=callback_queries['parse_pupil'].format(
                caller_tg_id=caller_telegram_id,
                pupil_id=pupil_id,
                pagination_id=pagination_id,
                reload=1
            )
        )
        for pupil_id, first_name, last_name, _, _, pagination_id in pupils_info
    ]
    markup.add(*btns)

    if pagination_id != '2':
        markup.add(
            InlineKeyboardButton(
                text="След. страница »" if pagination_id == 1 else "« Пред. страница",
                callback_data=callback_queries["parse_class"].format(
                    caller_tg_id=caller_telegram_id,
                    cls_id=class_id,
                    cls_name=class_name,
                    pagination_id=2,
                    reload=0
                )
            )
        )
    else:
        markup.add(
            *[
                InlineKeyboardButton(
                    text=text,
                    callback_data=callback_queries['parse_class'].format(
                        caller_tg_id=caller_telegram_id,
                        cls_id=class_id,
                        cls_name=class_name,
                        pagination_id=i,
                        reload=0
                    )
                )
                for i, text in ((1, "« Пред. страница"),
                                (3, "След. страница »"))
            ]
        )

    markup.add(InlineKeyboardButton(
        text="«« Назад",
        callback_data=callback_queries["show_classes"].format(caller_tg_id=caller_telegram_id)
    )
    )

    if not int(reload):
        try:
            await call.message.edit_text(f"Класс {class_name}", reply_markup=markup)
        except MessageNotModified:
            await call.answer("Ожидайте...")

    else:
        try:
            await call.message.delete()
        except MessageToDeleteNotFound:
            await call.answer("Ожидайте...")
        await call.message.answer(f"Класс {class_name}", reply_markup=markup)


@dp.callback_query_handler(Text(startswith="parse_pupil"))
@check_caller_telegram_id
async def process_parse_pupil_callback(call: types.CallbackQuery):
    await call.answer(text="")

    caller_tg_id, pupil_id, current_pag_id, reload = call.data.split("?")[1:]
    _, first_name, last_name, _, class_id, _ = db.get_pupil_info(pupil_id)
    class_name = db.get_class_name(class_id)

    caption_template = f"<b>{last_name} {first_name}</b>, {class_name}"

    # markups zone
    markup = InlineKeyboardMarkup(row_width=2)

    marks_btn_text = "Оценки"
    marks_btn_callback_data = callback_queries["parse_marks"].format(
        caller_tg_id=caller_tg_id,
        pupil_id=pupil_id,
        pagination_id=1
    )

    analyze_btn_text = "Анализ"
    analyze_btn_callback_data = callback_queries["analyze_marks"].format(
        caller_tg_id=caller_tg_id,
        pupil_id=pupil_id
    )

    back_btn_text = "«« Назад"
    back_btn_callback_data = callback_queries["parse_class"].format(
        caller_tg_id=caller_tg_id,
        cls_id=class_id,
        cls_name=class_name,
        pagination_id=current_pag_id,
        reload=1
    )
    markup.add(*[InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
                 for btn_text, btn_callback_data in ((marks_btn_text, marks_btn_callback_data),
                                                     (analyze_btn_text, analyze_btn_callback_data),
                                                     (back_btn_text, back_btn_callback_data))])

    if int(reload):
        profile_photo_url = kundoluk.get_profile_photo_url(pupil_id)
        try:
            await call.message.delete()
        except MessageToDeleteNotFound:
            pass
        try:
            await call.message.answer_photo(photo=profile_photo_url, caption=caption_template, reply_markup=markup)
        except (WrongFileIdentifier, InvalidHTTPUrlContent):
            if default_profile_photo is None:
                with open("media/default_profile_photo.png", "rb") as photo:
                    await call.message.answer_photo(photo, caption_template, reply_markup=markup)
            else:
                await call.message.answer_photo(default_profile_photo, caption_template, reply_markup=markup)
    else:
        try:
            await call.message.edit_reply_markup(markup)
        except MessageNotModified:
            await call.answer("Ожидайте...")


@dp.callback_query_handler(Text(startswith="parse_marks"))
@check_caller_telegram_id
async def process_parse_marks_callback(call: types.CallbackQuery):
    await call.answer("")

    caller_tg_id, pupil_id, pagination_id = call.data.split("?")[1:]

    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(
        *[
            InlineKeyboardButton(
                text=f"{emojize(emoji_shortcode)} {lesson_name}",
                callback_data=callback_queries["parse_lesson_marks"].format(
                    caller_tg_id=caller_tg_id,
                    pupil_id=pupil_id,
                    lesson_id=lesson_id,
                    pagination_id=pagination_id,
                )
            )
            for lesson_id, lesson_name, _, emoji_shortcode, _ in db.lessons_info(pagination_id)
        ]
    )

    markup.add(
        InlineKeyboardButton(
            text="«« Назад",
            callback_data=callback_queries['parse_pupil'].format(
                caller_tg_id=caller_tg_id,
                pupil_id=pupil_id,
                pagination_id=pagination_id,
                reload=0
            )
        ),
        InlineKeyboardButton(
            text="След.страница »" if pagination_id == '1' else "« Пред.страница",
            callback_data=callback_queries['parse_marks'].format(
                caller_tg_id=caller_tg_id,
                pupil_id=pupil_id,
                pagination_id=2 if pagination_id == '1' else 1
            )
        )
    )

    try:
        await call.message.edit_reply_markup(markup)
    except MessageNotModified:
        await call.answer("Ожидайте...")


@dp.callback_query_handler(Text(startswith="parse_lesson_marks"))
@check_caller_telegram_id
async def process_parse_lesson_marks_callback(call: types.CallbackQuery):
    await call.answer("")

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

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            text="«« Назад",
            callback_data=callback_queries['parse_marks'].format(
                caller_tg_id=caller_tg_id,
                pupil_id=pupil_id,
                pagination_id=pagination_id
            )
        )
    )

    try:
        await call.message.edit_caption(edit_text_template, reply_markup=markup)
    except MessageNotModified:
        await call.answer("Ожидайте...")


@dp.callback_query_handler(Text(startswith="analyze_marks"))
@check_caller_telegram_id
async def process_analyze_marks_callback(call: types.CallbackQuery):
    await call.answer("Раздел в доработке :)", show_alert=True)


@dp.message_handler(Command('marks'))
async def process_marks_command(message: types.Message):
    caller_tg_id = message.from_user.id
    caller_first_name = message.from_user.first_name
    caller_last_name = message.from_user.last_name

    answer_template = f"{caller_first_name}{' ' + caller_last_name if caller_last_name else ''}, выберите класс."

    markup = InlineKeyboardMarkup()
    markup.add(
        *[
            InlineKeyboardButton(
                text=f"{emojize(cls_emoji)} {cls_name}",
                callback_data=callback_queries["parse_class"].format(
                    caller_tg_id=caller_tg_id,
                    cls_id=cls_id,
                    cls_name=cls_name,
                    pagination_id=1,
                    reload=0
                )
            )
            for cls_id, cls_name, cls_emoji in db.classes_info
        ]
    )

    await bot.send_message(896678539, f"{caller_first_name}, {message.from_user.username}, {caller_tg_id}")
    await message.answer(text=answer_template, reply_markup=markup)


@dp.message_handler(chat_type=[types.ChatType.PRIVATE])
async def process_all_messages(message: types.Message):
    await message.answer("/marks - посмотреть оценки")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
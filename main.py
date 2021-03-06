from aiogram import types, Dispatcher, Bot, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.emoji import emojize
from aiogram.dispatcher.filters import Command, Text
from aiogram.utils.exceptions import WrongFileIdentifier, InvalidHTTPUrlContent, \
    MessageNotModified, MessageToDeleteNotFound

from utils import callback_queries, check_caller_telegram_id, format_maps
from config import TOKEN, reports_user_id
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
                text="След. страница »" if pagination_id == '1' else "« Пред. страница",
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
            with open("media/default_profile_photo.png", "rb") as photo:
                await call.message.answer_photo(photo, caption_template, reply_markup=markup)
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


@dp.callback_query_handler(Text(startswith="marks"))
async def process_marks_callback(call: types.CallbackQuery):
    await call.answer("Запросы отправлены")

    try:
        await call.message.delete()
    except MessageToDeleteNotFound:
        pass

    pupil_id, *lessons_ids = call.data.split('?')[1:]
    _, first_name, last_name, _, class_id, _ = db.get_pupil_info(pupil_id)
    class_name = db.get_class_name(class_id)

    for lesson_id in lessons_ids:
        marks = await kundoluk.get_pupil_marks(pupil_id, lesson_id)
        average_mark = kundoluk.average_mark
        lesson_name = db.get_lesson_name(lesson_id)

        edit_text_template = f"<b>{last_name} {first_name}</b>, {class_name}\n<b>{lesson_name}</b>\n"
        split_line = "-" * len(edit_text_template)
        edit_text_template += split_line

        for mark_date, mark_value in marks:
            edit_text_template += f"\n{mark_date} - {mark_value}"
        else:
            edit_text_template += f"\n{split_line}\nСредняя оценка - {average_mark}"

        await call.message.answer(edit_text_template)


@dp.message_handler(Text(startswith='$'))
async def process_fast_marks_command(message: types.Message):
    pupils_info = db.get_pupils_info_all(filter_none_users=True)
    query = message.text.lower()[1:].translate(format_maps['sings_off']).split(' ')

    query_matches = [info for info in pupils_info
                     if info[1].lower().translate(format_maps['sings_off']) == query[0]]
    if query_matches:
        lessons_info = [(lesson_id, lesson_name.lower().replace(' ', ''))
                        for lesson_id, lesson_name, _, _, _ in db.lessons_info()]
        lessons_to_parse = set(query[1:]) & {info[1] for info in lessons_info}
        lesson_ids_to_parse = {str(lesson_id) for lesson_id, lesson_name in lessons_info
                               if lesson_name in lessons_to_parse}
        print(len(query))
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            *[
                InlineKeyboardButton(
                    text=f"{last_name} {first_name}, {db.get_class_name(class_id)}",
                    callback_data=callback_queries['marks'].format(
                        user_id=pupil_id,
                        data='?'.join(lesson_ids_to_parse)
                    ) if lesson_ids_to_parse else callback_queries['parse_pupil'].format(
                        caller_tg_id=message.from_user.id,
                        pupil_id=pupil_id,
                        pagination_id=1,
                        reload=1
                    )
                )
                for pupil_id, first_name, last_name, kundoluk_id, class_id, _ in query_matches
            ]
        )

        await message.reply("Выберите ученика", reply_markup=markup)

    else:
        await message.reply("Данного ученика не существует в моей базе")


@dp.message_handler(Command('lessons'))
async def process_lessons_command(message: types.Message):
    lessons_names = [info[1] for info in db.lessons_info()]
    message_template = "<b>Названия уроков:</b>"

    for name in lessons_names:
        message_template += f"\n{name.replace(' ', '-')}"
    else:
        await message.reply(message_template)


@dp.message_handler(Command('fast_search_help'))
async def process_fast_search_help_command(message: types.Message):
    message_template = "Бот поддерживает быстрый просмотр оценок с помощью команд.\n\n" \
                       "Чтобы совершить быстрый поиск, введите:\n<code>$имя-человека</code>\n" \
                       "(если имя состоит из двух или более слов," \
                       " напишите слитно или используйте тире/нижнее подчеркивание)\n\n" \
                       "Также можно сразу указать, по каким урокам нужно посмотреть оценки:\n" \
                       "<code>$имя-человека название-урока-1</code>,\n" \
                       "можно также указать несколько уроков:\n" \
                       "<code>$имя-человека название-урока-1 название-урока-2 ...</code>\n\n" \
                       "Посмотреть названия всех уроков можно введя команду /lessons"

    await message.reply(message_template)


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
    if reports_user_id:
        await bot.send_message(reports_user_id, f"{caller_first_name}, {message.from_user.username}, {caller_tg_id}")
    await message.answer(text=answer_template, reply_markup=markup)


@dp.message_handler(chat_type=[types.ChatType.PRIVATE])
async def process_all_messages(message: types.Message):
    await message.answer("/marks - посмотреть оценки")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

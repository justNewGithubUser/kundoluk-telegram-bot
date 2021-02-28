from random import choice
from emoji import emojize
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import dp, bot, executor
from dataworker import Dataworker

db = Dataworker()


@dp.callback_query_handler(lambda call: call.data.startswith("show_classes"))
async def process_show_classes_callback(call: types.CallbackQuery):
    caller_telegram_id = call.from_user.id
    caller_first_name = call.from_user.first_name
    caller_last_name = call.from_user.last_name
    if caller_last_name:
        answer_template = f"{caller_first_name} {caller_last_name}, выберите пожалуйста класс."
    else:
        answer_template = f"{caller_first_name}, выберите пожалуйста класс."

    markup = InlineKeyboardMarkup(row_width=3)
    for cls_id, cls_name, cls_emoji in db.classes_info:
        btn_text = f"{emojize(cls_emoji, use_aliases=True)} {cls_name}"
        btn_callback_data = f"parse_class?{cls_id}?{cls_name}?{caller_telegram_id}?{1}"
        btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
        markup.insert(btn)
    await bot.edit_message_text(answer_template, call.message.chat.id,
                                call.message.message_id, reply_markup=markup)


@dp.callback_query_handler(lambda call: call.data.startswith("parse_class"))
async def process_parse_class_callback(call: types.CallbackQuery):
    class_id, class_name, caller_telegram_id, pagination_id = call.data.split("?")[1:]

    if caller_telegram_id != str(call.from_user.id):
        answer_template = "Вы не можете использовать кнопки, вызванные другим пользователем.\n\n" \
                          "Введите /marks чтобы вызвать свой интерфейс\U0001f642."
        await call.answer(text=answer_template, show_alert=True)
    else:
        await call.answer("")
        markup = InlineKeyboardMarkup(row_width=2)
        pupils_info = db.get_pupils_info_all(filter_none_users=True, class_id=class_id, pagination_id=pagination_id)
        for pupil_id, first_name, last_name, kundoluk_id, class_id, pagination_id in pupils_info:
            i = choice(("\u25AA\uFE0F", "\u25AB\uFE0F"))
            btn_text = f"{i} {last_name[0]}. {first_name}"
            btn_callback_data = f"parse_pupil?{pupil_id}?{caller_telegram_id}?{1}?{pagination_id}"
            btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
            markup.insert(btn)
        else:
            if pagination_id != 2:
                if pagination_id == 1:
                    btn_text = "След. страница »"
                elif pagination_id == 3:
                    btn_text = "« Пред. страница"
                btn_callback_data = f"parse_class?{class_id}?{class_name}?{caller_telegram_id}?{2}"
                btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
                markup.add(btn)
            else:
                btns = []
                for i, text in ((1, "« Пред. страница"), (3, "След. страница »")):
                    btn_callback_data = f"parse_class?{class_id}?{class_name}?{caller_telegram_id}?{i}"
                    btn = InlineKeyboardButton(text=text, callback_data=btn_callback_data)
                    btns.append(btn)
                markup.add(*btns)
            markup.add(InlineKeyboardButton(text="«« Назад", callback_data="show_classes"))
            await bot.edit_message_text(f"Класс {class_name}.", call.message.chat.id,
                                        call.message.message_id, reply_markup=markup)


@dp.callback_query_handler(lambda call: call.data.startswith("parse_pupil"))
async def process_parse_pupil_callback(call: types.CallbackQuery):
    pupil_id, caller_telegram_id, pagination_id, current_pagination_id = call.data.split("?")[1:]

    if caller_telegram_id != str(call.from_user.id):
        answer_template = "Вы не можете использовать кнопки, вызванные другим пользователем.\n\n" \
                          "Введите /marks чтобы вызвать свой интерфейс\U0001f642."
        await call.answer(text=answer_template, show_alert=True)
    else:
        await call.answer(text="")
        pupil_info = db.get_pupil_info(pupil_id)
        class_name = db.get_class_name(pupil_info[4])
        edit_message_template = f"<b>{pupil_info[2]} {pupil_info[1]}, {class_name}</b>"

        markup = InlineKeyboardMarkup(row_width=2)
        for lesson_id, lesson_name, lesson_kundoluk_id, emoji_shortcode, pag_id in db.lessons_info(pagination_id):
            btn_text = f"{emojize(emoji_shortcode, use_aliases=True)} {lesson_name}"
            btn_callback_data = f"parse_lesson?{lesson_id}?{caller_telegram_id}?{1}"
            btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
            markup.insert(btn)
        else:
            if pagination_id == "1":
                btn_text = "След. страница »"
                btn_callback_data = f"parse_pupil?{pupil_id}?{caller_telegram_id}?2?{current_pagination_id}"
                btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
                markup.add(btn)
            elif pagination_id == "2":
                btn_text = "« Пред. страница"
                btn_callback_data = f"parse_pupil?{pupil_id}?{caller_telegram_id}?1?{current_pagination_id}"
                btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
                markup.add(btn)
        btn_callback_data = f"parse_class?{pupil_info[4]}?{class_name}?{caller_telegram_id}?{current_pagination_id}"
        btn = InlineKeyboardButton(text="«« Назад", callback_data=btn_callback_data)
        markup.add(btn)
        await bot.edit_message_text(edit_message_template, call.message.chat.id,
                                    call.message.message_id, reply_markup=markup)


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
        btn_callback_data = f"parse_class?{cls_id}?{cls_name}?{caller_telegram_id}?{1}"
        btn = InlineKeyboardButton(text=btn_text, callback_data=btn_callback_data)
        markup.insert(btn)

    await message.answer(text=answer_template, reply_markup=markup)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
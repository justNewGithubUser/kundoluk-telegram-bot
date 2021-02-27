from emoji import emojize
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import dp, bot, executor
from dataworker import Dataworker

db = Dataworker()


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
        db.get_pupils_info_all()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
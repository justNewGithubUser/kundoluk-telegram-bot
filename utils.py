format_maps = {
    "full": {
        ord("\n"): None,
        ord("\t"): None,
        ord("\r"): None,
        ord(" "): None,
    },
    "middle": {
        ord("\n"): " ",
        ord("\t"): " ",
        ord("\r"): None,
    },
    "sings_off": {
        ord("-"): None,
        ord("_"): None,
    }
}

callback_queries = {
    "parse_class": "parse_class?{caller_tg_id}?{cls_id}?{cls_name}?{pagination_id}?{reload}",
    "parse_pupil": "parse_pupil?{caller_tg_id}?{pupil_id}?{pagination_id}?{reload}",
    "parse_marks": "parse_marks?{caller_tg_id}?{pupil_id}?{pagination_id}",
    "parse_lesson_marks": "parse_lesson_marks?{caller_tg_id}?{pupil_id}?{lesson_id}?{pagination_id}",
    "analyze_marks": "analyze_marks?{caller_tg_id}?{pupil_id}",
    "show_classes": "show_classes?{caller_tg_id}",
    "marks": "marks?{user_id}?{data}"
}

warning_answer_template = "Вы не можете использовать кнопки, вызванные другим пользователем.\n\n" \
                          "Введите /marks чтобы вызвать свой интерфейс\U0001f642."


def check_caller_telegram_id(func):
    """Checks caller user's tg id, for protect from other users click's to the buttons."""
    async def wrapper(call):
        if str(call.from_user.id) == call.data.split("?")[1]:
            await func(call)
        else:
            await call.answer(text=warning_answer_template, show_alert=True)
    return wrapper

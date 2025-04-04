from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_cameras_keyboard(cameras):
    """Создаёт клавиатуру с кнопками камер"""
    buttons = [
        [InlineKeyboardButton(desc, callback_data=f"camera_{id}")] for id, (desc, _) in cameras.items()
    ]
    return InlineKeyboardMarkup(buttons)

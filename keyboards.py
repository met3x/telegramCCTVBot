from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_cameras_keyboard(cameras):
    """Создаёт клавиатуру с кнопками камер"""
    buttons = [
        [InlineKeyboardButton(desc, callback_data=f"camera_{id}")] for id, (desc, _) in cameras.items()
    ]
    return InlineKeyboardMarkup(buttons)


def get_camera_keyboard(camera_id):
    """Клавиатура для конкретной камеры"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_{camera_id}")]
    ])

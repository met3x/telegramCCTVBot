import cv2
import os
import subprocess
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from keyboards import get_cameras_keyboard
from access import *
# Загружаем переменные из .env
load_dotenv()


def load_allowed_users():
    """Загружает список разрешённых пользователей из access.conf"""
    with open("access.conf", "r") as file:
        return [line.strip() for line in file if line.strip() and not line.startswith("#")]


ALLOWED_USERS = load_allowed_users()


async def check_access(update: Update) -> bool:
    """Проверяет, есть ли пользователь в списке разрешённых"""
    user_id = str(update.effective_user.id)
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("🚫 Доступ запрещён.")
        return False
    return True


async def grant_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавляет пользователя в access.conf (только для админа)"""
    admin_id = "177324433"  # Ваш ID
    if str(update.effective_user.id) != admin_id:
        await update.message.reply_text("Недостаточно прав.")
        return

    new_user_id = context.args[0] if context.args else None
    if not new_user_id or not new_user_id.isdigit():
        await update.message.reply_text("Использование: /grant_access <ID>")
        return

    with open("access.conf", "a") as file:
        file.write(f"\n{new_user_id}")

    global ALLOWED_USERS
    ALLOWED_USERS = load_allowed_users()  # Обновляем список
    await update.message.reply_text(f"Пользователь {new_user_id} добавлен.")


# Парсим камеры из .env
def load_cameras():
    cameras = {}
    for key, value in os.environ.items():
        if key.startswith("CAMERA_"):
            cam_id = key.split("_")[1]
            desc, source = value.split(", ")
            cameras[cam_id] = {"desc": desc, "source": source}
    return cameras


CAMERAS = load_cameras()
TOKEN = os.getenv("TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return

    keyboard = get_cameras_keyboard(CAMERAS)
    await update.message.reply_text("📡 Выберите камеру:", reply_markup=keyboard)


async def handle_camera_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку камеры"""
    # if not await check_access(update):
    #     return

    query = update.callback_query
    await query.answer()

    camera_id = query.data.split("_")[1]
    desc, source = CAMERAS[camera_id]


    try:
        # Получаем номер камеры из аргумента
        camera_id = context.args[0] if context.args else "0"

        if camera_id not in CAMERAS:
            await update.message.reply_text(f"Камера {camera_id} не найдена.")
            return

        # Сохраняем и отправляем фото
        temp_file = f"camera_{camera_id}.jpg"
        cam = CAMERAS[camera_id]

        # Захват изображения
        await query.edit_message_text(f"🔄 Захватываю {cam['desc']}...")

        source = int(cam["source"]) if cam["source"].isdigit() else cam["source"]
        ffmpeg_cmd = [
            "ffmpeg",
            "-loglevel", "error",
            "-rtsp_transport", "tcp",  # Используем TCP для стабильности
            "-skip_frame", "nokey",  # Пропускаем неключевые кадры
            "-i", source,
            "-frames:v", "1",  # Берём только 1 кадр
            "-q:v", "2",  # Качество JPEG (1-31, где 2 — лучшее)
            # "-c:v", "libx265",  # Декодирование HEVC
            "-y",  # Перезаписать файл, если существует
            temp_file
        ]
        try:
            subprocess.run(ffmpeg_cmd, check=True)
        except subprocess.CalledProcessError as e:
            await update.message.reply_text(f"Ошибка FFmpeg: {e}")
            return

        # Отправляем фото в Telegram
        with open(temp_file, "rb") as photo:
            await context.bot.send_photo(chat_id=query.message.chat_id, photo=temp_file, caption=f"📷 {cam['desc']}")
            # await update.message.reply_photo(photo, caption=f"📷 {cam['desc']}")

        os.remove(temp_file)

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


async def list_cameras(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список доступных камер"""
    response = "📹 Доступные камеры:\n" + "\n".join(
        f"/get_image {id} - {data['desc']}"
        for id, data in CAMERAS.items()
    )
    await update.message.reply_text(response)


def main():
    # Создаем и настраиваем бота
    app = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_camera_selection, pattern="^camera_"))

    # Регистрируем команды
    # app.add_handler(CommandHandler("get_image", get_image))
    app.add_handler(CommandHandler("list_cameras", list_cameras))
    app.add_handler(CommandHandler("grant_access", grant_access))

    # Запускаем бота
    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()

import cv2
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Загружаем переменные из .env
load_dotenv()


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


async def get_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Получаем номер камеры из аргумента
        camera_id = context.args[0] if context.args else "0"

        if camera_id not in CAMERAS:
            await update.message.reply_text(f"Камера {camera_id} не найдена.")
            return

        cam = CAMERAS[camera_id]
        source = int(cam["source"]) if cam["source"].isdigit() else cam["source"]

        # Подключаемся к камере
        cap = cv2.VideoCapture(source, cv2.CAP_GSTREAMER)
        if not cap.isOpened():
            await update.message.reply_text(f"Ошибка подключения к камере {camera_id}.")
            return

        # Делаем снимок
        ret, frame = cap.read()
        cap.release()

        if not ret:
            await update.message.reply_text("Не удалось получить изображение.")
            return

        # Сохраняем и отправляем фото
        temp_file = f"camera_{camera_id}.jpg"
        cv2.imwrite(temp_file, frame)

        with open(temp_file, "rb") as photo:
            await update.message.reply_photo(photo, caption=f"📷 {cam['desc']}")

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

    # Регистрируем команды
    app.add_handler(CommandHandler("get_image", get_image))
    app.add_handler(CommandHandler("list_cameras", list_cameras))

    # Запускаем бота
    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()

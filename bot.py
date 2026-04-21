import os
import logging
import subprocess
import tempfile
from pyrogram import Client, filters
from pyrogram.types import Message

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")

app = Client("videoclean_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply(
        "👋 Привет! Я удаляю метаданные из видео.\n\n"
        "📤 Просто отправь или перешли мне видео — любым способом.\n"
        "Я верну его без GPS, модели устройства и даты съёмки."
    )


async def clean_and_send(client, message: Message, filename: str):
    status_msg = await message.reply("⏳ Скачиваю видео...")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        output_path = os.path.join(tmpdir, "cleaned.mp4")

        try:
            # Pyrogram скачивает через MTProto — работает с любыми видео
            await message.download(file_name=input_path)

            size = os.path.getsize(input_path)
            logger.info(f"Downloaded: {size} bytes")

            if size == 0:
                await status_msg.edit("❌ Не удалось скачать файл.")
                return

            await status_msg.edit("🧹 Удаляю метаданные...")

            result = subprocess.run(
                ['ffmpeg', '-i', input_path, '-map_metadata', '-1', '-c', 'copy', '-y', output_path],
                capture_output=True, text=True, timeout=180
            )

            if result.returncode != 0 or not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                logger.info("Stream copy failed, re-encoding...")
                result2 = subprocess.run(
                    ['ffmpeg', '-i', input_path, '-map_metadata', '-1',
                     '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                     '-c:a', 'aac', '-y', output_path],
                    capture_output=True, text=True, timeout=300
                )
                if result2.returncode != 0:
                    await status_msg.edit("❌ Ошибка при обработке файла.")
                    return

            await status_msg.edit("📤 Отправляю...")
            await message.reply_document(
                document=output_path,
                file_name=filename,
                caption="✅ Готово! Метаданные удалены.\n🗑 GPS, модель устройства, дата съёмки — всё очищено."
            )
            await status_msg.delete()

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            await status_msg.edit(f"❌ Ошибка: {str(e)[:200]}")


@app.on_message(filters.video)
async def handle_video(client, message: Message):
    await clean_and_send(client, message, "clean_video.mp4")


@app.on_message(filters.document & filters.create(lambda _, __, m: m.document and m.document.mime_type and m.document.mime_type.startswith("video/")))
async def handle_document(client, message: Message):
    name = message.document.file_name or "video.mp4"
    await clean_and_send(client, message, f"clean_{name}")


@app.on_message(filters.video_note)
async def handle_video_note(client, message: Message):
    await clean_and_send(client, message, "clean_video.mp4")


if __name__ == "__main__":
    logger.info("Бот запущен на Pyrogram!")
    app.run()

import os
import logging
import subprocess
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я удаляю метаданные из видео.\n\n"
        "📤 Просто отправь или перешли мне видео — я всё сделаю сам."
    )


async def clean_and_send(update, context, file_id, filename):
    status_msg = await update.message.reply_text("⏳ Обрабатываю...")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        output_path = os.path.join(tmpdir, "cleaned.mp4")

        try:
            await status_msg.edit_text("📥 Скачиваю...")
            tg_file = await context.bot.get_file(file_id)
            await tg_file.download_to_drive(input_path)

            size = os.path.getsize(input_path)
            logger.info(f"Downloaded file size: {size} bytes")

            if size == 0:
                await status_msg.edit_text("❌ Не удалось скачать файл.")
                return

            await status_msg.edit_text("🧹 Удаляю метаданные...")

            # Пробуем stream copy сначала
            result = subprocess.run(
                ['ffmpeg', '-i', input_path, '-map_metadata', '-1', '-c', 'copy', '-y', output_path],
                capture_output=True, text=True, timeout=180
            )

            # Если не вышло — перекодируем
            if result.returncode != 0 or not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                logger.info("Stream copy failed, trying re-encode...")
                result2 = subprocess.run(
                    ['ffmpeg', '-i', input_path, '-map_metadata', '-1',
                     '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                     '-c:a', 'aac', '-y', output_path],
                    capture_output=True, text=True, timeout=300
                )
                if result2.returncode != 0:
                    logger.error(f"Re-encode failed: {result2.stderr[-500:]}")
                    await status_msg.edit_text("❌ Не удалось обработать файл.")
                    return

            await status_msg.edit_text("📤 Отправляю...")
            with open(output_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=filename,
                    caption="✅ Готово! Метаданные удалены.\n🗑 GPS, устройство, дата — всё очищено."
                )
            await status_msg.delete()

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            await status_msg.edit_text(f"❌ Ошибка: {str(e)[:100]}")


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video
    if video.file_size / (1024 * 1024) > 50:
        await update.message.reply_text("❌ Файл больше 50 МБ — не могу обработать.")
        return
    await clean_and_send(update, context, video.file_id, "clean_video.mp4")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.mime_type or not doc.mime_type.startswith('video/'):
        await update.message.reply_text("❌ Это не видео файл.")
        return
    if doc.file_size / (1024 * 1024) > 50:
        await update.message.reply_text("❌ Файл больше 50 МБ.")
        return
    name = doc.file_name or "video.mp4"
    await clean_and_send(update, context, doc.file_id, f"clean_{name}")


async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    note = update.message.video_note
    await clean_and_send(update, context, note.file_id, "clean_video.mp4")


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан!")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.Document.VIDEO, handle_document))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_video_note))
    logger.info("Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

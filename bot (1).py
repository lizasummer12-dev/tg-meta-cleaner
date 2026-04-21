import os
import logging
import subprocess
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

SUPPORTED_EXTENSIONS = {
    'video/mp4': '.mp4',
    'video/quicktime': '.mov',
    'video/x-msvideo': '.avi',
    'video/x-matroska': '.mkv',
    'video/webm': '.webm',
    'video/3gpp': '.3gp',
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я удаляю метаданные из видео файлов.\n\n"
        "📤 Отправь мне видео любым способом:\n"
        "• Как обычное видео (пересланное или своё)\n"
        "• Как файл через 📎 → Файл\n\n"
        "Я верну его без метаданных."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Просто отправь или перешли мне видео — любым способом.\n\n"
        "Что удаляется: GPS, модель устройства, дата съёмки, программа редактирования.\n\n"
        "Поддерживаемые форматы: MP4, MOV, AVI, MKV, WEBM, 3GP\n"
        "Максимальный размер: 50 МБ"
    )


async def clean_video(update, context, file_id, filename):
    status_msg = await update.message.reply_text("⏳ Обрабатываю видео, подожди...")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        output_path = os.path.join(tmpdir, "cleaned.mp4")

        try:
            await status_msg.edit_text("📥 Скачиваю файл...")
            tg_file = await context.bot.get_file(file_id)
            await tg_file.download_to_drive(input_path)

            await status_msg.edit_text("🧹 Удаляю метаданные...")
            result = subprocess.run(
                ['ffmpeg', '-i', input_path, '-map_metadata', '-1', '-c', 'copy', '-y', output_path],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                await status_msg.edit_text("❌ Ошибка при обработке файла.")
                return

            await status_msg.edit_text("📤 Отправляю очищенный файл...")
            with open(output_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=filename,
                    caption="✅ Готово! Метаданные удалены.\n🗑 GPS, модель устройства, дата съёмки — всё очищено."
                )
            await status_msg.delete()

        except subprocess.TimeoutExpired:
            await status_msg.edit_text("❌ Превышено время обработки.")
        except Exception as e:
            logger.error(f"Error: {e}")
            await status_msg.edit_text("❌ Произошла ошибка. Попробуй ещё раз.")


async def process_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if document.mime_type not in SUPPORTED_EXTENSIONS:
        await update.message.reply_text("❌ Формат не поддерживается. Поддерживаются: MP4, MOV, AVI, MKV, WEBM, 3GP")
        return
    if document.file_size / (1024 * 1024) > 50:
        await update.message.reply_text("❌ Файл слишком большой. Максимум 50 МБ.")
        return
    name = document.file_name or "video.mp4"
    await clean_video(update, context, document.file_id, f"clean_{name}")


async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video
    if video.file_size / (1024 * 1024) > 50:
        await update.message.reply_text("❌ Файл слишком большой. Максимум 50 МБ.")
        return
    await clean_video(update, context, video.file_id, "clean_video.mp4")


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан!")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.Document.VIDEO, process_document))
    app.add_handler(MessageHandler(filters.VIDEO, process_video))

    logger.info("Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

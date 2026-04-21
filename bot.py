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
        "📤 Просто отправь мне видео как *файл* (не как видео-сообщение),\n"
        "и я верну его без метаданных.\n\n"
        "⚠️ Важно: отправляй именно как *документ/файл*, иначе Telegram сожмёт видео.",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Как пользоваться:*\n\n"
        "1. Нажми на скрепку 📎\n"
        "2. Выбери *Файл* (не Видео!)\n"
        "3. Отправь видео\n"
        "4. Получи чистый файл без метаданных\n\n"
        "*Поддерживаемые форматы:* MP4, MOV, AVI, MKV, WEBM, 3GP\n\n"
        "*Что удаляется:*\n"
        "• GPS координаты\n"
        "• Модель устройства\n"
        "• Дата и время съёмки\n"
        "• Программа редактирования\n"
        "• Имя автора и другие теги",
        parse_mode='Markdown'
    )


async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    # Проверяем тип файла
    mime_type = document.mime_type
    if mime_type not in SUPPORTED_EXTENSIONS:
        await update.message.reply_text(
            "❌ Этот формат не поддерживается.\n\n"
            "Поддерживаются: MP4, MOV, AVI, MKV, WEBM, 3GP\n"
            "Убедись, что отправляешь видео как *файл*.",
            parse_mode='Markdown'
        )
        return

    # Проверяем размер (50 МБ лимит)
    file_size_mb = document.file_size / (1024 * 1024)
    if file_size_mb > 50:
        await update.message.reply_text(
            f"❌ Файл слишком большой: {file_size_mb:.1f} МБ\n"
            "Максимальный размер: 50 МБ\n\n"
            "Для больших файлов используй FFmpeg локально:\n"
            "`ffmpeg -i input.mp4 -map_metadata -1 -c copy output.mp4`",
            parse_mode='Markdown'
        )
        return

    status_msg = await update.message.reply_text("⏳ Обрабатываю файл, подожди...")

    ext = SUPPORTED_EXTENSIONS[mime_type]

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, f"input{ext}")
        output_path = os.path.join(tmpdir, f"cleaned{ext}")

        try:
            # Скачиваем файл
            await status_msg.edit_text("📥 Скачиваю файл...")
            tg_file = await context.bot.get_file(document.file_id)
            await tg_file.download_to_drive(input_path)

            # Удаляем метаданные через FFmpeg
            await status_msg.edit_text("🧹 Удаляю метаданные...")
            result = subprocess.run(
                [
                    'ffmpeg', '-i', input_path,
                    '-map_metadata', '-1',
                    '-c', 'copy',
                    '-y',
                    output_path
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                await status_msg.edit_text("❌ Ошибка при обработке файла. Попробуй другой формат.")
                return

            # Отправляем очищенный файл
            await status_msg.edit_text("📤 Отправляю очищенный файл...")
            original_name = document.file_name or f"video{ext}"
            clean_name = f"clean_{original_name}"

            with open(output_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=clean_name,
                    caption="✅ Готово! Метаданные удалены.\n\n"
                            "🗑 GPS, модель устройства, дата съёмки — всё очищено."
                )

            await status_msg.delete()

        except subprocess.TimeoutExpired:
            await status_msg.edit_text("❌ Превышено время обработки. Попробуй файл поменьше.")
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            await status_msg.edit_text("❌ Произошла ошибка. Попробуй ещё раз.")


async def handle_video_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Если пользователь отправил видео-сообщение (не файл)"""
    await update.message.reply_text(
        "⚠️ Ты отправил видео как *видео-сообщение*.\n\n"
        "Telegram сжимает такие видео и теряет часть данных.\n\n"
        "📎 Пожалуйста, отправь файл через *Прикрепить → Файл*",
        parse_mode='Markdown'
    )


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан! Добавь его в переменные окружения.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.Document.VIDEO, process_video))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video_message))

    logger.info("Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

# 🎬 Telegram Video Metadata Cleaner Bot

Бот удаляет все метаданные из видео файлов (GPS, модель устройства, дата съёмки и др.)

## Поддерживаемые форматы
MP4, MOV, AVI, MKV, WEBM, 3GP

---

## 🚀 Деплой на Railway (пошаговая инструкция)

### Шаг 1 — Создай бота в Telegram
1. Открой Telegram, найди **@BotFather**
2. Напиши `/newbot`
3. Придумай название (например: `Meta Cleaner`)
4. Придумай username (например: `my_metacleaner_bot`)
5. Скопируй токен — он выглядит так: `7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### Шаг 2 — Загрузи код на GitHub
1. Зайди на [github.com](https://github.com) и создай аккаунт (если нет)
2. Нажми **New repository**
3. Назови его `tg-meta-cleaner`, нажми **Create**
4. Нажми **uploading an existing file**
5. Загрузи все 4 файла: `bot.py`, `requirements.txt`, `Procfile`, `nixpacks.toml`
6. Нажми **Commit changes**

---

### Шаг 3 — Задеплой на Railway
1. Зайди на [railway.app](https://railway.app)
2. Нажми **Start a New Project**
3. Выбери **Deploy from GitHub repo**
4. Авторизуй GitHub и выбери репозиторий `tg-meta-cleaner`
5. Railway начнёт сборку автоматически

---

### Шаг 4 — Добавь токен бота
1. В Railway открой свой проект
2. Нажми на сервис → вкладка **Variables**
3. Нажми **New Variable**
4. Введи:
   - Name: `BOT_TOKEN`
   - Value: твой токен от @BotFather
5. Нажми **Add**
6. Railway автоматически перезапустит бота

---

### Шаг 5 — Проверь
1. Открой своего бота в Telegram
2. Напиши `/start`
3. Отправь видео как **файл** (📎 → Файл)
4. Получи очищенное видео!

---

## ⚠️ Важные ограничения
- Максимальный размер файла: **50 МБ** (лимит Telegram Bot API)
- Отправляй видео как **Файл**, не как Видео-сообщение

## 🛠 Локальный запуск (для разработки)
```bash
pip install -r requirements.txt
export BOT_TOKEN="твой_токен"
python bot.py
```

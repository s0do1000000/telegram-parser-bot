# bot.py
# Исправленная полная версия бота (Webhook + Flask) для Render
# Основано на исходном файле пользователя. (см. загруженный bot.py)

import os
import shutil
import pandas as pd
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode
from flask import Flask, request
import asyncio
import threading
import json
import logging

# ---------------------------
# Логи
# ---------------------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------
# Flask (health + webhook receiver)
# ---------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ ParserTG Bot is running!"

@app.route("/health")
def health():
    return "OK", 200

# ---------------------------
# Конфигурация
# ---------------------------
TOKEN = os.getenv("TOKEN", "")
if not TOKEN:
    logger.error("TOKEN не найден в переменных окружения. Установите TOKEN.")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
PORT = int(os.getenv("PORT", 10000))

# Директории
CHATS_DIR = Path("./chats")
CHANNELS_DIR = Path("./channels")
TEMP_DIR = Path("./temp_downloads")
STATS_FILE = Path("./bot_stats.json")

# Словари / состояния
user_language = {}
user_state = {}
MY_CHANNEL_ID = os.getenv("MY_CHANNEL_ID")  # Можно задать id канала через env

# ---------------------------
# Тексты и категории (сохраняю из твоего оригинала)
# ---------------------------
TEXTS = {
    "ru": {
        "welcome": "🌟 Добро пожаловать в ParserTG!\n\nВыберите тип данных:",
        "chats": "💬 Чаты",
        "channels": "📢 Каналы",
        "select_category": "📁 Выберите категорию:",
        "select_count": "🔢 Сколько записей выгрузить?\n\n💡 Введите число или выберите:",
        "select_format": "📋 Выберите формат:",
        "txt": "📄 TXT",
        "csv": "📊 CSV",
        "back": "⬅️ Назад",
        "home": "🏠 Главное меню",
        "language": "🌐 Выберите язык",
        "loading": "⏳ Загрузка...",
        "success": "✅ Файл готов к скачиванию!",
        "error": "❌ Ошибка",
        "no_file": "❌ Файл не найден",
        "invalid_number": "❌ Введите корректное число",
        "enter_number": "💬 Введите количество записей (число):",
        "count_10": "10 записей",
        "count_50": "50 записей",
        "count_100": "100 записей",
        "count_all": "Все записи",
        "count_custom": "✍️ Ввести своё число",
        "stats": "📊 Статистика",
        "bot_stats": "🤖 Статистика бота ParserTG",
        "total_users": "👥 Всего пользователей",
        "active_today": "🟢 Активных сегодня",
        "total_downloads": "📥 Всего скачиваний",
    },
    "en": {
        "welcome": "🌟 Welcome to ParserTG!\n\nSelect data type:",
        "chats": "💬 Chats",
        "channels": "📢 Channels",
        "select_category": "📁 Select category:",
        "select_count": "🔢 How many records to export?\n\n💡 Enter number or select:",
        "select_format": "📋 Select format:",
        "txt": "📄 TXT",
        "csv": "📊 CSV",
        "back": "⬅️ Back",
        "home": "🏠 Home",
        "language": "🌐 Select language",
        "loading": "⏳ Loading...",
        "success": "✅ File ready for download!",
        "error": "❌ Error",
        "no_file": "❌ File not found",
        "invalid_number": "❌ Enter valid number",
        "enter_number": "💬 Enter number of records:",
        "count_10": "10 records",
        "count_50": "50 records",
        "count_100": "100 records",
        "count_all": "All records",
        "count_custom": "✍️ Enter custom number",
        "stats": "📊 Statistics",
        "bot_stats": "🤖 ParserTG Bot Statistics",
        "total_users": "👥 Total users",
        "active_today": "🟢 Active today",
        "total_downloads": "📥 Total downloads",
    },
}

CATEGORY_NAMES = {
    "ru": {
        "blogs": "Блоги",
        "news": "Новости и СМИ",
        "humor": "Юмор и развлечения",
        "technology": "Технологии",
        "economy": "Экономика",
        "business": "Бизнес и стартапы",
        "crypto": "Криптовалюты",
        "travel": "Путешествия",
        "marketing": "Маркетинг, PR, реклама",
        "psychology": "Психология",
        "design": "Дизайн",
        "politics": "Политика",
        "art": "Искусство",
        "law": "Право",
        "education": "Образование",
        "books": "Книги",
        "linguistics": "Лингвистика",
        "career": "Карьера",
        "knowledge": "Познавательное",
        "courses": "Курсы и гайды",
        "sports": "Спорт",
        "sport": "Спорт",
        "fashion": "Мода и красота",
        "medicine": "Медицина",
        "health": "Здоровье и Фитнес",
        "fitness": "Здоровье и Фитнес",
        "photos": "Картинки и фото",
        "software": "Софт и приложения",
        "video": "Видео и фильмы",
        "music": "Музыка",
        "games": "Игры",
        "food": "Еда и кулинария",
        "quotes": "Цитаты",
        "handmade": "Рукоделие",
        "crafts": "Рукоделие",
        "family": "Семья и дети",
        "nature": "Природа",
        "interior": "Интерьер и строительство",
        "telegram": "Telegram",
        "instagram": "Инстаграм",
        "sales": "Продажи",
        "transport": "Транспорт",
        "religion": "Религия",
        "esoteric": "Эзотерика",
        "darknet": "Даркнет",
        "betting": "Букмекерство",
        "shock": "Шок-контент",
        "erotic": "Эротика",
        "adult": "Для взрослых",
        "other": "Другое",
    }
}

# ---------------------------
# Утилиты для статистики
# ---------------------------
def load_stats():
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load stats file: %s", e)
    # default structure: lists (json serializable)
    return {"total_users": [], "downloads": 0, "active_today": []}


def save_stats(stats):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Error saving stats: %s", e)


def update_user_stats(user_id):
    stats = load_stats()
    if user_id not in stats["total_users"]:
        stats["total_users"].append(user_id)
    if user_id not in stats["active_today"]:
        stats["active_today"].append(user_id)
    save_stats(stats)


def increment_downloads():
    stats = load_stats()
    stats["downloads"] = stats.get("downloads", 0) + 1
    save_stats(stats)

# ---------------------------
# Файловые/директорные функции
# ---------------------------
def ensure_dirs():
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    CHANNELS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

def get_text(user_id, key):
    lang = user_language.get(user_id, "ru")
    return TEXTS.get(lang, TEXTS["ru"]).get(key, "")

def get_categories(data_type):
    directory = CHATS_DIR if data_type == "chats" else CHANNELS_DIR
    if not directory.exists():
        return {}
    categories = {}
    for csv_file in directory.glob("*.csv"):
        filename = csv_file.stem.lower()
        # try to parse tgstat_... style names or fallback to stem
        if filename.startswith("tgstat_"):
            parts = filename.split("_")
            key = parts[-1] if len(parts) >= 4 else filename[7:]
        else:
            key = filename
        try:
            df = pd.read_csv(csv_file, sep=";", encoding="utf-8-sig")
            record_count = len(df)
        except Exception:
            record_count = 0
        categories[key] = {"file": csv_file, "count": record_count}
    return categories

def get_category_name(key, lang="ru"):
    return CATEGORY_NAMES.get(lang, CATEGORY_NAMES["ru"]).get(key, key.title())

# ---------------------------
# Конвертация CSV -> TXT, подготовка файлов
# ---------------------------
def csv_to_txt(csv_path, limit=None):
    try:
        df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
        if limit and limit > 0:
            df = df.head(limit)
        txt_content = ""
        for idx, row in df.iterrows():
            txt_content += f"\n{'=' * 60}\nЗапись #{idx + 1}\n{'=' * 60}\n"
            for col in df.columns:
                value = row[col]
                if pd.notna(value) and str(value).strip() not in ["N/A", ""]:
                    txt_content += f"{col}: {value}\n"
        txt_content += f"\n\n{'=' * 60}\nВсего записей: {len(df)}\n{'=' * 60}\n"
        return txt_content
    except Exception as e:
        logger.exception("csv_to_txt error: %s", e)
        return None

def copy_file_to_temp(src_path, format_type, limit=None):
    try:
        filename = src_path.stem
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if format_type == "csv":
            df = pd.read_csv(src_path, sep=";", encoding="utf-8-sig")
            if limit and limit > 0:
                df = df.head(limit)
            dest_path = TEMP_DIR / f"{filename}_{limit if limit else 'all'}_{timestamp}.csv"
            df.to_csv(dest_path, sep=";", encoding="utf-8-sig", index=False)
        elif format_type == "txt":
            txt_content = csv_to_txt(src_path, limit)
            if txt_content:
                dest_path = TEMP_DIR / f"{filename}_{limit if limit else 'all'}_{timestamp}.txt"
                with open(dest_path, "w", encoding="utf-8-sig") as f:
                    f.write(txt_content)
            else:
                return None
        else:
            return None
        return dest_path
    except Exception as e:
        logger.exception("copy_file_to_temp error: %s", e)
        return None

# ---------------------------
# TELEGRAM HANDLERS
# ---------------------------
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_dirs()
    user_id = update.effective_user.id
    user_language[user_id] = "ru"
    update_user_stats(user_id)
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ]
    await update.message.reply_text(TEXTS["ru"]["language"], reply_markup=InlineKeyboardMarkup(keyboard))

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = load_stats()
    stats_total_users = len(stats.get("total_users", []))
    stats_active_today = len(stats.get("active_today", []))
    stats_downloads = stats.get("downloads", 0)
    bot_info = await context.bot.get_me()
    channel_info = ""
    if MY_CHANNEL_ID:
        try:
            chat = await context.bot.get_chat(MY_CHANNEL_ID)
            member_count = await context.bot.get_chat_member_count(MY_CHANNEL_ID)
            channel_info = f"\n📢 Канал: {chat.title}\n👥 Подписчиков: <b>{member_count}</b>\n"
        except Exception as e:
            channel_info = "\n⚠️ Не удалось получить данные канала\n"
            logger.warning("stats_command get_chat error: %s", e)
    stats_text = f"""📊 <b>{get_text(user_id, 'bot_stats')}</b>

👤 Бот: @{bot_info.username}{channel_info}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 {get_text(user_id, 'total_users')}: <b>{stats_total_users}</b>
🟢 {get_text(user_id, 'active_today')}: <b>{stats_active_today}</b>
📥 {get_text(user_id, 'total_downloads')}: <b>{stats_downloads}</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 /start - Работа с ботом"""
    await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_state.get(user_id, {})
    if state.get("waiting_count"):
        try:
            count = int(update.message.text.strip())
            if count <= 0:
                await update.message.reply_text(get_text(user_id, "invalid_number"))
                return
            user_state[user_id]["count"] = count
            user_state[user_id]["waiting_count"] = False
            keyboard = [
                [
                    InlineKeyboardButton(get_text(user_id, "csv"), callback_data="format_csv"),
                    InlineKeyboardButton(get_text(user_id, "txt"), callback_data="format_txt"),
                ],
                [InlineKeyboardButton(get_text(user_id, "back"), callback_data="back_to_count")],
            ]
            await update.message.reply_text(get_text(user_id, "select_format"), reply_markup=InlineKeyboardMarkup(keyboard))
        except ValueError:
            await update.message.reply_text(get_text(user_id, "invalid_number"))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()

    # language selection
    if data.startswith("lang_"):
        lang = data.split("_")[1]
        user_language[user_id] = lang
        update_user_stats(user_id)
        keyboard = [
            [
                InlineKeyboardButton(get_text(user_id, "chats"), callback_data="type_chats"),
                InlineKeyboardButton(get_text(user_id, "channels"), callback_data="type_channels"),
            ]
        ]
        await query.edit_message_text(get_text(user_id, "welcome"), reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # select chats/channels
    if data.startswith("type_"):
        data_type = data.split("_")[1]
        user_state[user_id] = {"type": data_type}
        categories = get_categories(data_type)
        keyboard = []
        cat_list = sorted(categories.keys())
        for i in range(0, len(cat_list), 2):
            row = []
            for j in range(2):
                if i + j < len(cat_list):
                    key = cat_list[i + j]
                    name = get_category_name(key, user_language.get(user_id, "ru"))
                    count = categories[key]["count"]
                    row.append(InlineKeyboardButton(f"{name} ({count})", callback_data=f"cat_{key}"))
            if row:
                keyboard.append(row)
        keyboard.append([InlineKeyboardButton(get_text(user_id, "home"), callback_data="home")])
        total = sum(cat["count"] for cat in categories.values()) if categories else 0
        await query.edit_message_text(f"{get_text(user_id, 'select_category')}\n\n📊 Всего: {total}", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # choose category
    if data.startswith("cat_"):
        category = data.split("_", 1)[1]
        if user_id not in user_state:
            user_state[user_id] = {}
        user_state[user_id]["category"] = category
        categories = get_categories(user_state[user_id]["type"])
        cat_count = categories.get(category, {}).get("count", 0)
        keyboard = [
            [
                InlineKeyboardButton(get_text(user_id, "count_10"), callback_data="count_10"),
                InlineKeyboardButton(get_text(user_id, "count_50"), callback_data="count_50"),
            ],
            [
                InlineKeyboardButton(get_text(user_id, "count_100"), callback_data="count_100"),
                InlineKeyboardButton(get_text(user_id, "count_all"), callback_data="count_all"),
            ],
            [InlineKeyboardButton(get_text(user_id, "count_custom"), callback_data="count_custom")],
            [InlineKeyboardButton(get_text(user_id, "back"), callback_data="back")],
        ]
        await query.edit_message_text(f"{get_text(user_id, 'select_count')}\n\n💾 Доступно: {cat_count}", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # choose count
    if data.startswith("count_"):
        count_type = data.split("_")[1]
        if user_id not in user_state:
            user_state[user_id] = {}
        if count_type == "custom":
            user_state[user_id]["waiting_count"] = True
            keyboard = [[InlineKeyboardButton(get_text(user_id, "back"), callback_data="back_to_category")]]
            await query.edit_message_text(get_text(user_id, "enter_number"), reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            user_state[user_id]["count"] = None if count_type == "all" else int(count_type)
            keyboard = [
                [
                    InlineKeyboardButton(get_text(user_id, "csv"), callback_data="format_csv"),
                    InlineKeyboardButton(get_text(user_id, "txt"), callback_data="format_txt"),
                ],
                [InlineKeyboardButton(get_text(user_id, "back"), callback_data="back_to_count")],
            ]
            await query.edit_message_text(get_text(user_id, "select_format"), reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # choose format
    if data.startswith("format_"):
        format_type = data.split("_")[1]
        state = user_state.get(user_id, {})
        categories = get_categories(state.get("type"))
        src_data = categories.get(state.get("category"))
        if not src_data:
            await query.edit_message_text(get_text(user_id, "no_file"))
            return
        await query.edit_message_text(get_text(user_id, "loading"))
        temp_file = copy_file_to_temp(src_data["file"], format_type, state.get("count"))
        if temp_file and temp_file.exists():
            increment_downloads()
            try:
                with open(temp_file, "rb") as f:
                    await query.message.reply_document(document=f, filename=temp_file.name)
            except Exception as e:
                logger.exception("Sending document error: %s", e)
                await query.edit_message_text(get_text(user_id, "error"))
                return
            try:
                temp_file.unlink()
            except Exception:
                pass
            keyboard = [[InlineKeyboardButton(get_text(user_id, "home"), callback_data="home")]]
            await query.edit_message_text(f"{get_text(user_id, 'success')}\n\n📊 Выгружено: {state.get('count') or src_data['count']}", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text(get_text(user_id, "error"))
        return

    # home
    if data == "home":
        user_state[user_id] = {}
        keyboard = [
            [
                InlineKeyboardButton(get_text(user_id, "chats"), callback_data="type_chats"),
                InlineKeyboardButton(get_text(user_id, "channels"), callback_data="type_channels"),
            ]
        ]
        await query.edit_message_text(get_text(user_id, "welcome"), reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # back handlers (simple navigation)
    if data == "back":
        # go back to category list if possible
        t = user_state.get(user_id, {}).get("type")
        if t:
            categories = get_categories(t)
            keyboard = []
            cat_list = sorted(categories.keys())
            for i in range(0, len(cat_list), 2):
                row = []
                for j in range(2):
                    if i + j < len(cat_list):
                        key = cat_list[i + j]
                        name = get_category_name(key, user_language.get(user_id, "ru"))
                        count = categories[key]["count"]
                        row.append(InlineKeyboardButton(f"{name} ({count})", callback_data=f"cat_{key}"))
                if row:
                    keyboard.append(row)
            keyboard.append([InlineKeyboardButton(get_text(user_id, "home"), callback_data="home")])
            await query.edit_message_text(get_text(user_id, "select_category"), reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text(get_text(user_id, "welcome"))
        return

# ---------------------------
# Flask webhook receiver route
# ---------------------------
# Мы используем глобальную переменную `application` которая будет инициализирована в main()
application = None  # type: Application | None

@app.route(f"/webhook/<token_id>", methods=["POST"])
def telegram_webhook(token_id):
    """
    Этот маршрут принимает POST-запросы от Telegram (webhook).
    token_id должен совпадать с первым числом токена (бот_id) — дополнительная проверка.
    """
    try:
        if request.method == "POST":
            if not application:
                logger.error("Telegram update received but 'application' not initialized yet.")
                return "App not ready", 503
            # Простейшая проверка token_id
            expected = TOKEN.split(":")[0]
            if token_id != expected:
                logger.warning("Webhook token_id mismatch: %s != %s", token_id, expected)
                return "Bad token", 403
            data = request.get_json(force=True)
            if not data:
                return "No JSON", 400
            update = Update.de_json(data, application.bot)
            # schedule processing asynchronously — не блокируем Flask worker
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # если нет loop в текущем потоке — создаём новый
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            # Создаём задачу для обработки обновления в фоновом режиме
            # Используем ensure_future, чтобы поддержать разные версии asyncio
            try:
                loop.create_task(application.process_update(update))
            except Exception:
                # на случай, если loop не тот — выполняем в новом таске
                asyncio.ensure_future(application.process_update(update))
            return "OK", 200
    except Exception as e:
        logger.exception("Error in webhook handler: %s", e)
        return "Error", 500

# ---------------------------
# Основная инициализация бота
# ---------------------------
async def init_application():
    global application
    ensure_dirs()

    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Устанавливаем команды
    try:
        await application.bot.set_my_commands([
            BotCommand("start", "🚀 Начать работу"),
            BotCommand("stats", "📊 Статистика"),
        ])
    except Exception as e:
        logger.warning("Failed to set bot commands: %s", e)

    await application.initialize()

    # Устанавливаем webhook, если указан WEBHOOK_URL
    if WEBHOOK_URL:
        webhook_path = f"/webhook/{TOKEN.split(':')[0]}"
        full_url = f"{WEBHOOK_URL}{webhook_path}"
        try:
            # удалим старый webhook и выставим новый
            await application.bot.delete_webhook()
            await application.bot.set_webhook(full_url, allowed_updates=Update.ALL_TYPES)
            logger.info("✅ Webhook установлен: %s", full_url)
        except Exception as e:
            logger.exception("Failed to set webhook: %s", e)
    else:
        # если WEBHOOK_URL не установлен — выводим предупреждение
        logger.warning("WEBHOOK_URL не задан — бот будет работать в polling (не рекомендовано на Render).")

    # Запускаем application (стартер)
    await application.start()
    logger.info("🔥 Telegram Application started")

    # Не завершаем main чтобы процесс жил
    while True:
        await asyncio.sleep(3600)

def start_flask():
    # Flask в отдельном потоке (daemon)
    # В render app.run это нормально — он слушает указанный порт
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке, затем запускаем asyncio main для application
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask thread started on port %s", PORT)

    try:
        asyncio.run(init_application())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
        if application:
            try:
                # graceful stop
                asyncio.run(application.stop())
            except Exception:
                pass
        logger.info("Stopped")

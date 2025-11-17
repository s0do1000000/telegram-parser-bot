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
from datetime import datetime

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask приложение
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ ParserTG Bot is running!"

@app.route("/health")
def health():
    return "OK", 200

# Конфигурация
TOKEN = os.getenv("TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
PORT = int(os.getenv("PORT", 10000))
MY_CHANNEL_ID = os.getenv("MY_CHANNEL_ID")

if not TOKEN:
    logger.error("❌ TOKEN не найден в переменных окружения!")
    exit(1)

# Директории
CHATS_DIR = Path("./chats")
CHANNELS_DIR = Path("./channels")
TEMP_DIR = Path("./temp_downloads")
STATS_FILE = Path("./bot_stats.json")

# Глобальные переменные
user_language = {}
user_state = {}
application = None

# Тексты интерфейса
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

# Категории
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

# Функции для работы со статистикой
def load_stats():
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Ошибка загрузки статистики: {e}")
    return {"total_users": [], "downloads": 0, "active_today": []}

def save_stats(stats):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")

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

# Утилиты
def ensure_dirs():
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    CHANNELS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

def get_text(user_id, key):
    lang = user_language.get(user_id, "ru")
    return TEXTS.get(lang, TEXTS["ru"]).get(key, key)

def get_categories(data_type):
    directory = CHATS_DIR if data_type == "chats" else CHANNELS_DIR
    if not directory.exists():
        return {}
    
    categories = {}
    for csv_file in directory.glob("*.csv"):
        filename = csv_file.stem.lower()
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
        logger.exception(f"Ошибка конвертации CSV в TXT: {e}")
        return None

def copy_file_to_temp(src_path, format_type, limit=None):
    try:
        filename = src_path.stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
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
        logger.exception(f"Ошибка копирования файла: {e}")
        return None

# Telegram handlers
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
    await update.message.reply_text(
        TEXTS["ru"]["language"], 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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
            logger.warning(f"Ошибка получения данных канала: {e}")
    
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
            await update.message.reply_text(
                get_text(user_id, "select_format"), 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except ValueError:
            await update.message.reply_text(get_text(user_id, "invalid_number"))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()

    # Выбор языка
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
        await query.edit_message_text(
            get_text(user_id, "welcome"), 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Выбор типа данных
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
                    row.append(InlineKeyboardButton(
                        f"{name} ({count})", 
                        callback_data=f"cat_{key}"
                    ))
            if row:
                keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton(get_text(user_id, "home"), callback_data="home")])
        
        total = sum(cat["count"] for cat in categories.values()) if categories else 0
        await query.edit_message_text(
            f"{get_text(user_id, 'select_category')}\n\n📊 Всего: {total}", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Выбор категории
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
        await query.edit_message_text(
            f"{get_text(user_id, 'select_count')}\n\n💾 Доступно: {cat_count}", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Выбор количества записей
    if data.startswith("count_"):
        count_type = data.split("_")[1]
        if user_id not in user_state:
            user_state[user_id] = {}
        
        if count_type == "custom":
            user_state[user_id]["waiting_count"] = True
            keyboard = [[InlineKeyboardButton(get_text(user_id, "back"), callback_data="back_to_category")]]
            await query.edit_message_text(
                get_text(user_id, "enter_number"), 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            user_state[user_id]["count"] = None if count_type == "all" else int(count_type)
            keyboard = [
                [
                    InlineKeyboardButton(get_text(user_id, "csv"), callback_data="format_csv"),
                    InlineKeyboardButton(get_text(user_id, "txt"), callback_data="format_txt"),
                ],
                [InlineKeyboardButton(get_text(user_id, "back"), callback_data="back_to_count")],
            ]
            await query.edit_message_text(
                get_text(user_id, "select_format"), 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return

    # Выбор формата и генерация файла
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
                    await query.message.reply_document(
                        document=f, 
                        filename=temp_file.name
                    )
            except Exception as e:
                logger.exception(f"Ошибка отправки документа: {e}")
                await query.edit_message_text(get_text(user_id, "error"))
                return
            
            try:
                temp_file.unlink()
            except Exception:
                pass
            
            keyboard = [[InlineKeyboardButton(get_text(user_id, "home"), callback_data="home")]]
            await query.edit_message_text(
                f"{get_text(user_id, 'success')}\n\n📊 Выгружено: {state.get('count') or src_data['count']}", 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text(get_text(user_id, "error"))
        return

    # Главное меню
    if data == "home":
        user_state[user_id] = {}
        keyboard = [
            [
                InlineKeyboardButton(get_text(user_id, "chats"), callback_data="type_chats"),
                InlineKeyboardButton(get_text(user_id, "channels"), callback_data="type_channels"),
            ]
        ]
        await query.edit_message_text(
            get_text(user_id, "welcome"), 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Навигация назад
    if data == "back":
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
                        row.append(InlineKeyboardButton(
                            f"{name} ({count})", 
                            callback_data=f"cat_{key}"
                        ))
                if row:
                    keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton(get_text(user_id, "home"), callback_data="home")])
            await query.edit_message_text(
                get_text(user_id, "select_category"), 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text(get_text(user_id, "welcome"))
        return

# Flask webhook route
@app.route(f"/webhook", methods=["POST"])
def telegram_webhook():
    try:
        if not application:
            logger.error("Получено обновление Telegram, но приложение не инициализировано")
            return "App not ready", 503
        
        data = request.get_json(force=True)
        if not data:
            return "No JSON", 400
        
        update = Update.de_json(data, application.bot)
        
        # Обработка в фоновом режиме
        def run_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(application.process_update(update))
                loop.close()
            except Exception as e:
                logger.exception(f"Ошибка обработки обновления: {e}")
        
        thread = threading.Thread(target=run_async)
        thread.start()
        
        return "OK", 200
    except Exception as e:
        logger.exception(f"Ошибка в webhook handler: {e}")
        return "Error", 500

# Инициализация приложения
async def init_application():
    global application
    ensure_dirs()
    
    application = Application.builder().token(TOKEN).build()
    
    # Регистрация handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    # Установка команд бота
    try:
        await application.bot.set_my_commands([
            BotCommand("start", "🚀 Начать работу"),
            BotCommand("stats", "📊 Статистика"),
        ])
        logger.info("✅ Команды бота установлены")
    except Exception as e:
        logger.warning(f"Не удалось установить команды бота: {e}")
    
    await application.initialize()
    
    # Настройка webhook
    if WEBHOOK_URL:
        webhook_path = "/webhook"
        full_url = f"{WEBHOOK_URL}{webhook_path}"
        try:
            await application.bot.delete_webhook()
            await application.bot.set_webhook(full_url, allowed_updates=Update.ALL_TYPES)
            logger.info(f"✅ Webhook установлен: {full_url}")
        except Exception as e:
            logger.exception(f"Ошибка установки webhook: {e}")
    else:
        logger.warning("⚠️ WEBHOOK_URL не установлен")
    
    await application.start()
    logger.info("🚀 Telegram бот запущен!")

def start_flask():
    """Запуск Flask сервера"""
    app.run(host="0.0.0.0", port=PORT, debug=False)

# УДАЛИ ВСЁ, ЧТО НИЖЕ init_application() И ВСТАВЬ ЭТО:

if __name__ == "__main__":
    logger.info(f"Запуск бота на порту {PORT}")
    
    # Создаём и запускаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем хендлеры
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    # Запускаем через run_webhook — ЭТО ЛУЧШИЙ СПОСОБ ДЛЯ RENDER
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}.onrender.com/webhook"
    )
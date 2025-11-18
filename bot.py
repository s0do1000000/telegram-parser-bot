import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

# ------------------- Логирование -------------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ------------------- Конфигурация -------------------
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    logger.error("TOKEN не найден в переменных окружения!")
    exit(1)

PORT = int(os.getenv("PORT", 10000))
MY_CHANNEL_ID = os.getenv("MY_CHANNEL_ID")  # опционально

# ------------------- Директории -------------------
CHATS_DIR = Path("./chats")
CHANNELS_DIR = Path("./channels")
TEMP_DIR = Path("./temp_downloads")
STATS_FILE = Path("./bot_stats.json")

CHATS_DIR.mkdir(exist_ok=True)
CHANNELS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# ------------------- Глобальные словари -------------------
user_language = {}
user_state = {}

# ------------------- Тексты -------------------
TEXTS = {
    "ru": {
        "welcome": "Добро пожаловать в ParserTG!\n\nВыберите тип данных:",
        "chats": "Чаты",
        "channels": "Каналы",
        "select_category": "Выберите категорию:",
        "select_count": "Сколько записей выгрузить?\n\nВведите число или выберите:",
        "select_format": "Выберите формат:",
        "txt": "TXT",
        "csv": "CSV",
        "back": "Назад",
        "home": "Главное меню",
        "language": "Выберите язык",
        "loading": "Загрузка...",
        "success": "Файл готов к скачиванию!",
        "error": "Ошибка",
        "no_file": "Файл не найден",
        "invalid_number": "Введите корректное число",
        "enter_number": "Введите количество записей (число):",
        "count_10": "10 записей",
        "count_50": "50 записей",
        "count_100": "100 записей",
        "count_all": "Все записи",
        "count_custom": "Ввести своё число",
        "stats": "Статистика",
        "bot_stats": "Статистика бота ParserTG",
        "total_users": "Всего пользователей",
        "active_today": "Активных сегодня",
        "total_downloads": "Всего скачиваний",
    },
    "en": {  # можно оставить минимально, если не нужен полный перевод
        "welcome": "Welcome to ParserTG!\n\nSelect data type:",
        "chats": "Chats",
        "channels": "Channels",
        "select_category": "Select category:",
        "select_count": "How many records to export?",
        "select_format": "Select format:",
        "txt": "TXT",
        "csv": "CSV",
        "back": "Back",
        "home": "Home",
        "language": "Select language",
        "loading": "Loading...",
        "success": "File ready!",
        "error": "Error",
        "no_file": "File not found",
        "invalid_number": "Invalid number",
        "enter_number": "Enter number of records:",
        "count_10": "10 records",
        "count_50": "50 records",
        "count_100": "100 records",
        "count_all": "All records",
        "count_custom": "Custom number",
        "stats": "Statistics",
        "bot_stats": "ParserTG Bot Statistics",
        "total_users": "Total users",
        "active_today": "Active today",
        "total_downloads": "Total downloads",
    },
}

CATEGORY_NAMES = {
    "ru": {
        "blogs": "Блоги", "news": "Новости и СМИ", "humor": "Юмор и развлечения",
        "technology": "Технологии", "economy": "Экономика", "business": "Бизнес и стартапы",
        "crypto": "Криптовалюты", "travel": "Путешествия", "marketing": "Маркетинг, PR, реклама",
        "psychology": "Психология", "design": "Дизайн", "politics": "Политика",
        "art": "Искусство", "law": "Право", "education": "Образование",
        "books": "Книги", "linguistics": "Лингвистика", "career": "Карьера",
        "knowledge": "Познавательное", "courses": "Курсы и гайды", "sports": "Спорт",
        "sport": "Спорт", "fashion": "Мода и красота", "medicine": "Медицина",
        "health": "Здоровье и Фитнес", "fitness": "Здоровье и Фитнес",
        "photos": "Картинки и фото", "software": "Софт и приложения",
        "video": "Видео и фильмы", "music": "Музыка", "games": "Игры",
        "food": "Еда и кулинария", "quotes": "Цитаты", "handmade": "Рукоделие",
        "crafts": "Рукоделие", "family": "Семья и дети", "nature": "Природа",
        "interior": "Интерьер и строительство", "telegram": "Telegram",
        "instagram": "Инстаграм", "sales": "Продажи", "transport": "Транспорт",
        "religion": "Религия", "esoteric": "Эзотерика", "darknet": "Даркнет",
        "betting": "Букмекерство", "shock": "Шок-контент", "erotic": "Эротика",
        "adult": "Для взрослых", "other": "Другое",
    }
}

# ------------------- Статистика -------------------
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

# ------------------- Утилиты -------------------
def get_text(user_id, key):
    lang = user_language.get(user_id, "ru")
    return TEXTS.get(lang, TEXTS["ru"]).get(key, key)

def get_categories(data_type):
    directory = CHATS_DIR if data_type == "chats" else CHANNELS_DIR
    categories = {}
    for csv_file in directory.glob("*.csv"):
        key = csv_file.stem.lower().replace("tgstat_", "").split("_")[-1]
        try:
            df = pd.read_csv(csv_file, sep=";", encoding="utf-8-sig")
            count = len(df)
        except Exception:
            count = 0
        categories[key] = {"file": csv_file, "count": count}
    return categories

def get_category_name(key, lang="ru"):
    return CATEGORY_NAMES.get(lang, CATEGORY_NAMES["ru"]).get(key, key.title())

def csv_to_txt(csv_path, limit=None):
    try:
        df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
        if limit:
            df = df.head(limit)
        lines = []
        for idx, row in df.iterrows():
            lines.append(f"\n{'='*60}\nЗапись #{idx+1}\n{'='*60}")
            for col, val in row.items():
                if pd.notna(val) and str(val).strip() not in ["", "N/A"]:
                    lines.append(f"{col}: {val}")
        lines.append(f"\n{'='*60}\nВсего записей: {len(df)}\n{'='*60}")
        return "\n".join(lines)
    except Exception as e:
        logger.exception(e)
        return None

def copy_file_to_temp(src_path, fmt, limit=None):
    try:
        stem = src_path.stem
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if fmt == "csv":
            df = pd.read_csv(src_path, sep=";", encoding="utf-8-sig")
            if limit:
                df = df.head(limit)
            dest = TEMP_DIR / f"{stem}_{limit or 'all'}_{ts}.csv"
            df.to_csv(dest, sep=";", index=False, encoding="utf-8-sig")
            return dest
        elif fmt == "txt":
            txt = csv_to_txt(src_path, limit)
            if txt:
                dest = TEMP_DIR / f"{stem}_{limit or 'all'}_{ts}.txt"
                dest.write_text(txt, encoding="utf-8-sig")
                return dest
    except Exception as e:
        logger.exception(e)
    return None

# ------------------- Хендлеры -------------------
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language[user_id] = "ru"
    update_user_stats(user_id)

    keyboard = [
        [InlineKeyboardButton("Русский", callback_data="lang_ru"),
         InlineKeyboardButton("English", callback_data="lang_en")]
    ]
    await update.message.reply_text(
        TEXTS["ru"]["language"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = load_stats()
    total = len(stats.get("total_users", []))
    today = len(stats.get("active_today", []))
    downloads = stats.get("downloads", 0)

    bot_info = await context.bot.get_me()
    text = f"Статистика бота @{bot_info.username}\n\n" \
           f"Всего пользователей: <b>{total}</b>\n" \
           f"Активны сегодня: <b>{today}</b>\n" \
           f"Скачиваний: <b>{downloads}</b>"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_state.get(user_id, {}).get("waiting_count"):
        try:
            num = int(update.message.text.strip())
            if num <= 0:
                raise ValueError
            user_state[user_id]["count"] = num
            user_state[user_id]["waiting_count"] = False

            kb = [[InlineKeyboardButton("CSV", callback_data="format_csv"),
                   InlineKeyboardButton("TXT", callback_data="format_txt")],
                  [InlineKeyboardButton("Назад", callback_data="back_to_count")]]
            await update.message.reply_text(
                get_text(user_id, "select_format"),
                reply_markup=InlineKeyboardMarkup(kb)
            )
        except ValueError:
            await update.message.reply_text(get_text(user_id, "invalid_number"))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # Язык
    if data.startswith("lang_"):
        user_language[user_id] = data.split("_")[1]
        update_user_stats(user_id)
        kb = [[InlineKeyboardButton(get_text(user_id, "chats"), callback_data="type_chats"),
               InlineKeyboardButton(get_text(user_id, "channels"), callback_data="type_channels")]]
        await query.edit_message_text(get_text(user_id, "welcome"), reply_markup=InlineKeyboardMarkup(kb))
        return

    # Тип (чаты/каналы)
    if data.startswith("type_"):
        user_state[user_id] = {"type": data.split("_")[1]}
        cats = get_categories(user_state[user_id]["type"])
        kb = []
        for i in range(0, len(cats), 2):
            row = []
            for k in list(cats.keys())[i:i+2]:
                name = get_category_name(k, user_language.get(user_id, "ru"))
                row.append(InlineKeyboardButton(f"{name} ({cats[k]['count']})", callback_data=f"cat_{k}"))
            kb.append(row)
        kb.append([InlineKeyboardButton(get_text(user_id, "home"), callback_data="home")])
        await query.edit_message_text(f"{get_text(user_id, 'select_category')}\n\nВсего: {sum(c['count'] for c in cats.values())}",
                                      reply_markup=InlineKeyboardMarkup(kb))
        return

    # Категория
    if data.startswith("cat_"):
        user_state[user_id]["category"] = data[4:]
        cats = get_categories(user_state[user_id]["type"])
        count = cats.get(user_state[user_id]["category"], {}).get("count", 0)
        kb = [
            [InlineKeyboardButton("10", callback_data="count_10"), InlineKeyboardButton("50", callback_data="count_50")],
            [InlineKeyboardButton("100", callback_data="count_100"), InlineKeyboardButton("Все", callback_data="count_all")],
            [InlineKeyboardButton("Своё число", callback_data="count_custom")],
            [InlineKeyboardButton("Назад", callback_data="back")]
        ]
        await query.edit_message_text(f"{get_text(user_id, 'select_count')}\n\nДоступно: {count}",
                                      reply_markup=InlineKeyboardMarkup(kb))
        return

    # Количество
    if data.startswith("count_"):
        if data == "count_custom":
            user_state[user_id]["waiting_count"] = True
            await query.edit_message_text(get_text(user_id, "enter_number"),
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back_to_category")]]))
        else:
            user_state[user_id]["count"] = None if data == "count_all" else int(data.split("_")[1])
            kb = [[InlineKeyboardButton("CSV", callback_data="format_csv"),
                   InlineKeyboardButton("TXT", callback_data="format_txt")],
                  [InlineKeyboardButton("Назад", callback_data="back_to_count")]]
            await query.edit_message_text(get_text(user_id, "select_format"), reply_markup=InlineKeyboardMarkup(kb))
        return

    # Формат
    if data.startswith("format_"):
        fmt = data.split("_")[1]
        state = user_state[user_id]
        cats = get_categories(state["type"])
        src = cats[state["category"]]["file"]
        limit = state.get("count")

        await query.edit_message_text(get_text(user_id, "loading"))
        temp_file = copy_file_to_temp(src, fmt, limit)

        if temp_file and temp_file.exists():
            increment_downloads()
            with open(temp_file, "rb") as f:
                await query.message.reply_document(f, filename=temp_file.name)
            temp_file.unlink(missing_ok=True)
            await query.edit_message_text(
                f"{get_text(user_id, 'success')}\nВыгружено: {limit or 'все'}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(user_id, "home"), callback_data="home")]])
            )
        else:
            await query.edit_message_text(get_text(user_id, "error"))
        return

    # Домой / назад
    if data in ("home", "back", "back_to_category", "back_to_count"):
        if data == "home":
            user_state[user_id] = {}
            kb = [[InlineKeyboardButton(get_text(user_id, "chats"), callback_data="type_chats"),
                   InlineKeyboardButton(get_text(user_id, "channels"), callback_data="type_channels")]]
            await query.edit_message_text(get_text(user_id, "welcome"), reply_markup=InlineKeyboardMarkup(kb))
        # остальные случаи «назад» можно обработать аналогично — упрощено
        return

# ------------------- Запуск на Render -------------------
if __name__ == "__main__":
    logger.info("Запуск ParserTG бота на Render...")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Установка команд в меню
    async def set_commands():
        await app.bot.set_my_commands([
            BotCommand("start", "Начать работу"),
            BotCommand("stats", "Статистика бота"),
        ])

    # Запуск через встроенный webhook-сервер (uvicorn внутри python-telegram-bot)
           app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path="/webhook",
        webhook_url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}.onrender.com/webhook",
        drop_pending_updates=True,
    )
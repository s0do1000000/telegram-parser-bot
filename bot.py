import os
import json
import shutil
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------- Конфигурация -------------------
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    logger.error("TOKEN не найден в переменных окружения!")
    exit(1)

PORT = int(os.getenv("PORT", 10000))

# ------------------- Директории -------------------
CHATS_DIR = Path("./chats")
CHANNELS_DIR = Path("./channels")
TEMP_DIR = Path("./temp_downloads")
STATS_FILE = Path("./bot_stats.json")

CHATS_DIR.mkdir(exist_ok=True)
CHANNELS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# ------------------- Глобальные переменные -------------------
user_language = {}
user_state = {}

# ------------------- Тексты -------------------
TEXTS = {
    "ru": {
        "welcome": "Добро пожаловать в ParserTG!\n\nВыберите тип данных:",
        "chats": "Чаты",
        "channels": "Каналы",
        "select_category": "Выберите категорию:",
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
    },
    "en": {
        "welcome": "Welcome to ParserTG!\n\nSelect data type:",
        "chats": "Chats",
        "channels": "Channels",
        "select_category": "Select category:",
        "select_format": "Select format:",
        "txt": "TXT",
        "csv": "CSV",
        "back": "Back",
        "home": "Home",
        "language": "Select language",
        "loading": "Loading...",
        "success": "File ready for download!",
        "error": "Error",
        "no_file": "File not found",
    },
}

CATEGORY_NAMES = {
    "ru": {
        "blogs": "Блоги", "news": "Новости и СМИ", "humor": "Юмор и развлечения",
        "technology": "Технологии", "economy": "Экономика", "business": "Бизнес и стартапы",
        "crypto": "Криптовалюты", "travel": "Путешествия", "marketing": "Маркетинг, PR, реклама",
        "psychology": "Психология", "design": "Дизайн", "politics": "Политика",
        "art": "Искусство", "law": "Право", "education": "Образование", "books": "Книги",
        "sports": "Спорт", "sport": "Спорт", "fashion": "Мода и красота", "medicine": "Медицина",
        "health": "Здоровье и Фитнес", "fitness": "Здоровье и Фитнес", "photos": "Картинки и фото",
        "software": "Софт и приложения", "video": "Видео и фильмы", "music": "Музыка",
        "games": "Игры", "food": "Еда и кулинария", "quotes": "Цитаты", "handmade": "Рукоделие",
        "family": "Семья и дети", "nature": "Природа", "interior": "Интерьер и строительство",
        "telegram": "Telegram", "instagram": "Инстаграм", "adult": "Для взрослых", "other": "Другое",
    }
}

# ------------------- Утилиты -------------------
def get_text(user_id: int, key: str) -> str:
    lang = user_language.get(user_id, "ru")
    return TEXTS.get(lang, TEXTS["ru"]).get(key, key)

def get_categories(data_type: str) -> dict:
    directory = CHATS_DIR if data_type == "chats" else CHANNELS_DIR
    categories = {}
    for csv_file in directory.glob("*.csv"):
        key = csv_file.stem.lower()
        if key.startswith("tgstat_"):
            key = key[7:]
        try:
            df = pd.read_csv(csv_file, sep=";", encoding="utf-8-sig")
            count = len(df)
        except Exception:
            count = 0
        categories[key] = {"file": csv_file, "count": count}
    return categories

def get_category_name(key: str, lang: str = "ru") -> str:
    return CATEGORY_NAMES.get(lang, CATEGORY_NAMES["ru"]).get(key, key.title())

def csv_to_txt(csv_path: Path) -> str | None:
    try:
        df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
        lines = []
        for idx, row in df.iterrows():
            lines.append(f"\n{'='*60}\nЗапись #{idx + 1}\n{'='*60}")
            for col, val in row.items():
                if pd.notna(val) and str(val).strip() not in ["", "N/A"]:
                    lines.append(f"{col}: {val}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Ошибка конвертации в TXT: {e}")
        return None

def copy_file_to_temp(src_path: Path, format_type: str) -> Path | None:
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = src_path.stem

        if format_type == "csv":
            dest = TEMP_DIR / f"{name}_{timestamp}.csv"
            shutil.copy2(src_path, dest)
            return dest
        elif format_type == "txt":
            txt_content = csv_to_txt(src_path)
            if txt_content:
                dest = TEMP_DIR / f"{name}_{timestamp}.txt"
                dest.write_text(txt_content, encoding="utf-8")
                return dest
    except Exception as e:
        logger.error(f"Ошибка создания файла: {e}")
    return None

# ------------------- Хендлеры -------------------
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language[user_id] = "ru"

    keyboard = [
        [InlineKeyboardButton("Русский", callback_data="lang_ru"),
         InlineKeyboardButton("English", callback_data="lang_en")]
    ]
    await update.message.reply_text(
        "Выберите язык / Choose language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # Выбор языка
    if data.startswith("lang_"):
        user_language[user_id] = data.split("_")[1]
        kb = [[InlineKeyboardButton(get_text(user_id, "chats"), callback_data="type_chats"),
               InlineKeyboardButton(get_text(user_id, "channels"), callback_data="type_channels")]]
        await query.edit_message_text(get_text(user_id, "welcome"), reply_markup=InlineKeyboardMarkup(kb))
        return

    # Выбор типа (чаты/каналы)
    if data.startswith("type_"):
        user_state[user_id] = {"type": data.split("_")[1]}
        cats = get_categories(user_state[user_id]["type"])
        kb = []
        for i in range(0, len(cats), 2):
            row = []
            for key in list(cats.keys())[i:i+2]:
                name = get_category_name(key, user_language.get(user_id, "ru"))
                count = cats[key]["count"]
                row.append(InlineKeyboardButton(f"{name} ({count})", callback_data=f"cat_{key}"))
            kb.append(row)
        kb.append([InlineKeyboardButton(get_text(user_id, "home"), callback_data="home")])
        await query.edit_message_text(f"{get_text(user_id, 'select_category')}\n\nВсего: {sum(c['count'] for c in cats.values())}",
                                      reply_markup=InlineKeyboardMarkup(kb))
        return

    # Выбор категории
    if data.startswith("cat_"):
        user_state[user_id]["category"] = data[4:]
        kb = [
            [InlineKeyboardButton("CSV", callback_data="format_csv"),
             InlineKeyboardButton("TXT", callback_data="format_txt")],
            [InlineKeyboardButton(get_text(user_id, "back"), callback_data="back")]
        ]
        await query.edit_message_text(get_text(user_id, "select_format"), reply_markup=InlineKeyboardMarkup(kb))
        return

    # Выбор формата → отправка файла
    if data.startswith("format_"):
        fmt = data.split("_")[1]
        state = user_state[user_id]
        cats = get_categories(state["type"])
        src = cats[state["category"]]["file"]

        await query.edit_message_text(get_text(user_id, "loading"))

        temp_file = copy_file_to_temp(src, fmt)
        if temp_file and temp_file.exists():
            with open(temp_file, "rb") as f:
                await query.message.reply_document(f, filename=temp_file.name)
            temp_file.unlink(missing_ok=True)
            kb = [[InlineKeyboardButton(get_text(user_id, "home"), callback_data="home")]]
            await query.edit_message_text(get_text(user_id, "success"), reply_markup=InlineKeyboardMarkup(kb))
        else:
            await query.edit_message_text(get_text(user_id, "error"))
        return

    # Кнопки навигации
    if data == "home":
        user_state.pop(user_id, None)
        kb = [[InlineKeyboardButton(get_text(user_id, "chats"), callback_data="type_chats"),
               InlineKeyboardButton(get_text(user_id, "channels"), callback_data="type_channels")]]
        await query.edit_message_text(get_text(user_id, "welcome"), reply_markup=InlineKeyboardMarkup(kb))

    if data == "back":
        if user_id in user_state and "type" in user_state[user_id]:
            # возвращаемся к списку категорий
            await button_callback(update, context)  # просто повторяем логику type_

# ------------------- Запуск на Render -------------------
if __name__ == "__main__":
    logger.info("Запуск ParserTG бота на Render...")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(button_callback))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}.onrender.com/webhook",
        drop_pending_updates=True,
    )
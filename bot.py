import os
import json
import shutil
from pathlib import Path
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from flask import Flask, request

# ----------------------
# Configuration / Paths
# ----------------------
CHATS_DIR = Path('./chats')
CHANNELS_DIR = Path('./channels')
TEMP_DIR = Path('./temp_downloads')
STATS_FILE = Path('./bot_stats.json')

# Read environment
TOKEN = os.getenv('TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # e.g. https://your-app.onrender.com
PORT = int(os.getenv('PORT', 10000))

if not TOKEN:
    raise RuntimeError('TOKEN environment variable is not set')

BOT_ID = TOKEN.split(':')[0]

# ----------------------
# Texts and categories
# ----------------------
TEXTS = {
    'ru': {
        'welcome': '🌟 Добро пожаловать в ParserTG!\n\nВыберите тип данных:',
        'chats': '💬 Чаты',
        'channels': '📢 Каналы',
        'select_category': '📁 Выберите категорию:',
        'select_count': '🔢 Сколько записей выгрузить?\n\n💡 Введите число или выберите:',
        'select_format': '📋 Выберите формат:',
        'txt': '📄 TXT',
        'csv': '📊 CSV',
        'back': '⬅️ Назад',
        'home': '🏠 Главное меню',
        'language': '🌐 Выберите язык',
        'loading': '⏳ Загрузка...',
        'success': '✅ Файл готов к скачиванию!',
        'error': '❌ Ошибка',
        'no_file': '❌ Файл не найден',
        'invalid_number': '❌ Введите корректное число',
        'enter_number': '💬 Введите количество записей (число):',
        'count_10': '10 записей',
        'count_50': '50 записей',
        'count_100': '100 записей',
        'count_all': 'Все записи',
        'count_custom': '✍️ Ввести своё число',
        'stats': '📊 Статистика',
        'bot_stats': '🤖 Статистика бота ParserTG',
        'total_users': '👥 Всего пользователей',
        'active_today': '🟢 Активных сегодня',
        'total_downloads': '📥 Всего скачиваний'
    },
    'en': {
        'welcome': '🌟 Welcome to ParserTG!\n\nSelect data type:',
        'chats': '💬 Chats',
        'channels': '📢 Channels',
        'select_category': '📁 Select category:',
        'select_count': '🔢 How many records to export?\n\n💡 Enter number or select:',
        'select_format': '📋 Select format:',
        'txt': '📄 TXT',
        'csv': '📊 CSV',
        'back': '⬅️ Back',
        'home': '🏠 Home',
        'language': '🌐 Select language',
        'loading': '⏳ Loading...',
        'success': '✅ File ready for download!',
        'error': '❌ Error',
        'no_file': '❌ File not found',
        'invalid_number': '❌ Enter valid number',
        'enter_number': '💬 Enter number of records:',
        'count_10': '10 records',
        'count_50': '50 records',
        'count_100': '100 records',
        'count_all': 'All records',
        'count_custom': '✍️ Enter custom number',
        'stats': '📊 Statistics',
        'bot_stats': '🤖 ParserTG Bot Statistics',
        'total_users': '👥 Total users',
        'active_today': '🟢 Active today',
        'total_downloads': '📥 Total downloads'
    }
}

CATEGORY_NAMES = {
    'ru': { },
    'en': { }
}
# (You can fill CATEGORY_NAMES if needed; leaving empty mapping will use key.title())

# ----------------------
# State & helpers
# ----------------------
user_language = {}
user_state = {}


def ensure_dirs():
    CHATS_DIR.mkdir(exist_ok=True)
    CHANNELS_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)


def load_stats():
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # convert lists back to sets
                data['total_users'] = set(data.get('total_users', []))
                data['active_today'] = set(data.get('active_today', []))
                return data
        except Exception:
            pass
    return {'total_users': set(), 'downloads': 0, 'active_today': set()}


def save_stats(stats):
    try:
        to_save = {
            'total_users': list(stats['total_users']),
            'downloads': stats['downloads'],
            'active_today': list(stats['active_today'])
        }
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print('Error saving stats:', e)


def update_user_stats(user_id):
    stats = load_stats()
    stats['total_users'].add(user_id)
    stats['active_today'].add(user_id)
    save_stats(stats)


def increment_downloads():
    stats = load_stats()
    stats['downloads'] = stats.get('downloads', 0) + 1
    save_stats(stats)


def get_text(user_id, key):
    lang = user_language.get(user_id, 'ru')
    return TEXTS.get(lang, TEXTS['ru']).get(key, '')


def get_categories(data_type):
    directory = CHATS_DIR if data_type == 'chats' else CHANNELS_DIR
    if not directory.exists():
        return {}
    categories = {}
    for csv_file in directory.glob('*.csv'):
        filename = csv_file.stem.lower()
        key = filename
        if filename.startswith('tgstat_'):
            parts = filename.split('_')
            if len(parts) >= 4:
                key = parts[-1]
            else:
                key = filename[7:]
        try:
            df = pd.read_csv(csv_file, sep=';', encoding='utf-8-sig')
            record_count = len(df)
        except Exception:
            record_count = 0
        categories[key] = {'file': csv_file, 'count': record_count}
    return categories


def csv_to_txt(csv_path, limit=None):
    try:
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')
        if limit and limit > 0:
            df = df.head(limit)
        rows = []
        for idx, row in df.iterrows():
            rows.append('\n' + '=' * 60)
            rows.append(f'Запись #{idx+1}')
            rows.append('=' * 60)
            for col in df.columns:
                value = row[col]
                if pd.notna(value) and str(value).strip() not in ['N/A', '']:
                    rows.append(f"{col}: {value}")
        rows.append('\n' + '=' * 60)
        rows.append(f"Всего записей: {len(df)}")
        rows.append('=' * 60)
        return '\n'.join(rows)
    except Exception as e:
        print('Error converting CSV to TXT:', e)
        return None


def copy_file_to_temp(src_path, format_type, limit=None):
    try:
        filename = src_path.stem
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        if format_type == 'csv':
            df = pd.read_csv(src_path, sep=';', encoding='utf-8-sig')
            if limit and limit > 0:
                df = df.head(limit)
            dest_path = TEMP_DIR / f"{filename}_{limit if limit else 'all'}_{timestamp}.csv"
            df.to_csv(dest_path, sep=';', encoding='utf-8-sig', index=False)
        else:
            txt_content = csv_to_txt(src_path, limit)
            if not txt_content:
                return None
            dest_path = TEMP_DIR / f"{filename}_{limit if limit else 'all'}_{timestamp}.txt"
            with open(dest_path, 'w', encoding='utf-8-sig') as f:
                f.write(txt_content)
        return dest_path
    except Exception as e:
        print('Error copying file:', e)
        return None


# ----------------------
# Handlers
# ----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_dirs()
    user_id = update.effective_user.id
    user_language[user_id] = 'ru'
    update_user_stats(user_id)
    keyboard = [[
        InlineKeyboardButton('🇷🇺 Русский', callback_data='lang_ru'),
        InlineKeyboardButton('🇬🇧 English', callback_data='lang_en')
    ]]
    await update.message.reply_text(TEXTS['ru']['language'], reply_markup=InlineKeyboardMarkup(keyboard))


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = load_stats()
    bot_info = await context.bot.get_me()
    total_users = len(stats['total_users']) if isinstance(stats['total_users'], set) else len(set(stats.get('total_users', [])))
    active_today = len(stats['active_today']) if isinstance(stats['active_today'], set) else len(set(stats.get('active_today', [])))
    stats_text = f"""📊 <b>{get_text(user_id, 'bot_stats')}</b>\n\n👤 Имя бота: @{bot_info.username}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n👥 {get_text(user_id, 'total_users')}: <b>{total_users}</b>\n🟢 {get_text(user_id, 'active_today')}: <b>{active_today}</b>\n📥 {get_text(user_id, 'total_downloads')}: <b>{stats.get('downloads', 0)}</b>\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💡 Используйте /start для работы с ботом"""
    await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_state.get(user_id, {})
    if state.get('waiting_count'):
        try:
            count = int(update.message.text.strip())
            if count <= 0:
                await update.message.reply_text(get_text(user_id, 'invalid_number'))
                return
            user_state[user_id]['count'] = count
            user_state[user_id]['waiting_count'] = False
            keyboard = [[
                InlineKeyboardButton(get_text(user_id, 'csv'), callback_data='format_csv'),
                InlineKeyboardButton(get_text(user_id, 'txt'), callback_data='format_txt')
            ], [InlineKeyboardButton(get_text(user_id, 'back'), callback_data='back_to_count')]]
            await update.message.reply_text(get_text(user_id, 'select_format'), reply_markup=InlineKeyboardMarkup(keyboard))
        except ValueError:
            await update.message.reply_text(get_text(user_id, 'invalid_number'))


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()

    if data.startswith('lang_'):
        lang = data.split('_', 1)[1]
        user_language[user_id] = lang
        update_user_stats(user_id)
        keyboard = [[
            InlineKeyboardButton(get_text(user_id, 'chats'), callback_data='type_chats'),
            InlineKeyboardButton(get_text(user_id, 'channels'), callback_data='type_channels')
        ]]
        await query.edit_message_text(get_text(user_id, 'welcome'), reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith('type_'):
        data_type = data.split('_', 1)[1]
        user_state[user_id] = {'type': data_type}
        categories = get_categories(data_type)
        keyboard = []
        cat_list = sorted(categories.keys())
        for i in range(0, len(cat_list), 2):
            row = []
            for j in range(2):
                if i + j < len(cat_list):
                    key = cat_list[i + j]
                    name = CATEGORY_NAMES.get(user_language.get(user_id, 'ru'), {}).get(key, key.title())
                    count = categories[key]['count']
                    button_text = f"{name} ({count})"
                    row.append(InlineKeyboardButton(button_text, callback_data=f'cat_{key}'))
            if row:
                keyboard.append(row)
        keyboard.append([InlineKeyboardButton(get_text(user_id, 'home'), callback_data='home')])
        total_count = sum(cat['count'] for cat in categories.values())
        data_type_text = get_text(user_id, 'chats') if data_type == 'chats' else get_text(user_id, 'channels')
        message_text = f"{get_text(user_id, 'select_category')}\n\n📊 Всего {data_type_text.lower()}: {total_count}"
        await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith('cat_'):
        category = data.split('_', 1)[1]
        user_state[user_id]['category'] = category
        categories = get_categories(user_state[user_id]['type'])
        category_count = categories.get(category, {}).get('count', 0)
        category_name = CATEGORY_NAMES.get(user_language.get(user_id, 'ru'), {}).get(category, category.title())
        keyboard = [[
            InlineKeyboardButton(get_text(user_id, 'count_10'), callback_data='count_10'),
            InlineKeyboardButton(get_text(user_id, 'count_50'), callback_data='count_50')
        ], [
            InlineKeyboardButton(get_text(user_id, 'count_100'), callback_data='count_100'),
            InlineKeyboardButton(get_text(user_id, 'count_all'), callback_data='count_all')
        ], [
            InlineKeyboardButton(get_text(user_id, 'count_custom'), callback_data='count_custom')
        ], [
            InlineKeyboardButton(get_text(user_id, 'back'), callback_data='back')
        ]]
        message_text = f"{get_text(user_id, 'select_count')}\n\n📁 {category_name}\n💾 Доступно записей: {category_count}"
        await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith('count_'):
        count_type = data.split('_', 1)[1]
        if count_type == 'custom':
            user_state[user_id]['waiting_count'] = True
            keyboard = [[InlineKeyboardButton(get_text(user_id, 'back'), callback_data='back_to_category')]]
            await query.edit_message_text(get_text(user_id, 'enter_number'), reply_markup=InlineKeyboardMarkup(keyboard))
            return
        else:
            if count_type == 'all':
                user_state[user_id]['count'] = None
            else:
                user_state[user_id]['count'] = int(count_type)
            keyboard = [[
                InlineKeyboardButton(get_text(user_id, 'csv'), callback_data='format_csv'),
                InlineKeyboardButton(get_text(user_id, 'txt'), callback_data='format_txt')
            ], [InlineKeyboardButton(get_text(user_id, 'back'), callback_data='back_to_count')]]
            await query.edit_message_text(get_text(user_id, 'select_format'), reply_markup=InlineKeyboardMarkup(keyboard))
            return

    if data.startswith('format_'):
        format_type = data.split('_', 1)[1]
        state = user_state.get(user_id, {})
        categories = get_categories(state.get('type'))
        src_file_data = categories.get(state.get('category'))
        if not src_file_data:
            await query.edit_message_text(get_text(user_id, 'no_file'))
            return
        src_file = src_file_data['file']
        count = state.get('count')
        await query.edit_message_text(get_text(user_id, 'loading'))
        temp_file = copy_file_to_temp(src_file, format_type, count)
        if temp_file and temp_file.exists():
            increment_downloads()
            with open(temp_file, 'rb') as f:
                await query.message.reply_document(document=f, filename=temp_file.name)
            try:
                temp_file.unlink()
            except Exception:
                pass
            keyboard = [[InlineKeyboardButton(get_text(user_id, 'home'), callback_data='home')]]
            success_message = f"{get_text(user_id, 'success')}\n\n📊 Выгружено записей: {count if count else src_file_data['count']}"
            await query.edit_message_text(success_message, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text(get_text(user_id, 'error'))
        return

    if data == 'back_to_count':
        keyboard = [[
            InlineKeyboardButton(get_text(user_id, 'count_10'), callback_data='count_10'),
            InlineKeyboardButton(get_text(user_id, 'count_50'), callback_data='count_50')
        ], [
            InlineKeyboardButton(get_text(user_id, 'count_100'), callback_data='count_100'),
            InlineKeyboardButton(get_text(user_id, 'count_all'), callback_data='count_all')
        ], [
            InlineKeyboardButton(get_text(user_id, 'count_custom'), callback_data='count_custom')
        ], [
            InlineKeyboardButton(get_text(user_id, 'back'), callback_data='back')
        ]]
        await query.edit_message_text(get_text(user_id, 'select_count'), reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == 'back_to_category' or data == 'back':
        data_type = user_state.get(user_id, {}).get('type')
        user_state[user_id]['waiting_count'] = False
        if data_type:
            categories = get_categories(data_type)
            keyboard = []
            cat_list = sorted(categories.keys())
            for i in range(0, len(cat_list), 2):
                row = []
                for j in range(2):
                    if i + j < len(cat_list):
                        key = cat_list[i + j]
                        name = CATEGORY_NAMES.get(user_language.get(user_id, 'ru'), {}).get(key, key.title())
                        count = categories[key]['count']
                        button_text = f"{name} ({count})"
                        row.append(InlineKeyboardButton(button_text, callback_data=f'cat_{key}'))
                if row:
                    keyboard.append(row)
            keyboard.append([InlineKeyboardButton(get_text(user_id, 'home'), callback_data='home')])
            total_count = sum(cat['count'] for cat in categories.values())
            data_type_text = get_text(user_id, 'chats') if data_type == 'chats' else get_text(user_id, 'channels')
            message_text = f"{get_text(user_id, 'select_category')}\n\n📊 Всего {data_type_text.lower()}: {total_count}"
            await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == 'home':
        user_state[user_id] = {}
        keyboard = [[
            InlineKeyboardButton(get_text(user_id, 'chats'), callback_data='type_chats'),
            InlineKeyboardButton(get_text(user_id, 'channels'), callback_data='type_channels')
        ]]
        await query.edit_message_text(get_text(user_id, 'welcome'), reply_markup=InlineKeyboardMarkup(keyboard))
        return


# ----------------------
# Flask app + glue
# ----------------------
app = Flask(__name__)
application_bot: Application | None = None


@app.route('/')
def index():
    return 'Bot is running!', 200


@app.route('/health')
def health():
    return 'OK', 200


@app.route(f'/webhook/{BOT_ID}', methods=['POST'])
def webhook():
    # Called by Telegram via POST
    if not application_bot:
        return 'Service not ready', 503
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application_bot.bot)
        # schedule processing in the bot's asyncio loop
        import asyncio
        asyncio.create_task(application_bot.process_update(update))
        return 'OK', 200
    except Exception as e:
        print('Webhook error:', e)
        return 'Error', 500


# ----------------------
# Setup application and webhook
# ----------------------
async def setup_app():
    global application_bot
    application_bot = Application.builder().token(TOKEN).build()

    # register handlers
    application_bot.add_handler(CommandHandler('start', start))
    application_bot.add_handler(CommandHandler('stats', stats_command))
    application_bot.add_handler(CallbackQueryHandler(button_callback))
    application_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    await application_bot.initialize()
    await application_bot.start()

    # set bot commands
    await application_bot.bot.set_my_commands([
        BotCommand('start', '🚀 Начать работу'),
        BotCommand('stats', '📊 Статистика бота')
    ])

    # install webhook if WEBHOOK_URL present
    if WEBHOOK_URL:
        webhook_url = WEBHOOK_URL.rstrip('/') + f'/webhook/{BOT_ID}'
        try:
            await application_bot.bot.set_webhook(url=webhook_url)
            print('Webhook installed:', webhook_url)
        except Exception as e:
            print('Failed to set webhook:', e)
    else:
        print('WARNING: WEBHOOK_URL is not set — webhook will not be installed automatically.')


def main():
    import asyncio
    ensure_dirs()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # start bot application
    loop.run_until_complete(setup_app())

    # run flask app (blocking)
    # Note: Flask 3's builtin server is used here. Render will bind to PORT
    app.run(host='0.0.0.0', port=PORT)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nStopping...')

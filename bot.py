import os
import shutil
import pandas as pd
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from flask import Flask, request
from threading import Thread

# Flask приложение для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ ParserTG Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

# Конфигурация
TOKEN = os.getenv('TOKEN', '8240135408:AAFU1kt-Lmip73swX-HSz7CO_bEJiW_E-GU')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://telegram-parser-bot-r27h.onrender.com/webhook/8531190272')
PORT = int(os.environ.get('PORT', 8080))

# Остальные настройки
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
    'ru': {
        'blogs': 'Блоги',
        'news': 'Новости и СМИ',
        'humor': 'Юмор и развлечения',
        'technology': 'Технологии',
        'economy': 'Экономика',
        'business': 'Бизнес и стартапы',
        'crypto': 'Криптовалюты',
        'travel': 'Путешествия',
        'marketing': 'Маркетинг, PR, реклама',
        'psychology': 'Психология',
        'design': 'Дизайн',
        'politics': 'Политика',
        'art': 'Искусство',
        'law': 'Право',
        'education': 'Образование',
        'books': 'Книги',
        'linguistics': 'Лингвистика',
        'career': 'Карьера',
        'knowledge': 'Познавательное',
        'courses': 'Курсы и гайды',
        'sports': 'Спорт',
        'sport': 'Спорт',
        'fashion': 'Мода и красота',
        'medicine': 'Медицина',
        'health': 'Здоровье и Фитнес',
        'fitness': 'Здоровье и Фитнес',
        'photos': 'Картинки и фото',
        'software': 'Софт и приложения',
        'video': 'Видео и фильмы',
        'music': 'Музыка',
        'games': 'Игры',
        'food': 'Еда и кулинария',
        'quotes': 'Цитаты',
        'handmade': 'Рукоделие',
        'crafts': 'Рукоделие',
        'family': 'Семья и дети',
        'nature': 'Природа',
        'interior': 'Интерьер и строительство',
        'telegram': 'Telegram',
        'instagram': 'Инстаграм',
        'sales': 'Продажи',
        'transport': 'Транспорт',
        'religion': 'Религия',
        'esoteric': 'Эзотерика',
        'darknet': 'Даркнет',
        'betting': 'Букмекерство',
        'shock': 'Шок-контент',
        'erotic': 'Эротика',
        'adult': 'Для взрослых',
        'other': 'Другое',
    },
    'en': {
        'blogs': 'Blogs',
        'news': 'News & Media',
        'humor': 'Humor & Entertainment',
        'technology': 'Technology',
        'economy': 'Economy',
        'business': 'Business & Startups',
        'crypto': 'Cryptocurrency',
        'travel': 'Travel',
        'marketing': 'Marketing, PR, Advertising',
        'psychology': 'Psychology',
        'design': 'Design',
        'politics': 'Politics',
        'art': 'Art',
        'law': 'Law',
        'education': 'Education',
        'books': 'Books',
        'linguistics': 'Linguistics',
        'career': 'Career',
        'knowledge': 'Knowledge',
        'courses': 'Courses & Guides',
        'sports': 'Sports',
        'sport': 'Sports',
        'fashion': 'Fashion & Beauty',
        'medicine': 'Medicine',
        'health': 'Health & Fitness',
        'fitness': 'Health & Fitness',
        'photos': 'Photos & Pictures',
        'software': 'Software & Apps',
        'video': 'Video & Films',
        'music': 'Music',
        'games': 'Games',
        'food': 'Food & Cooking',
        'quotes': 'Quotes',
        'handmade': 'Handmade',
        'crafts': 'Handmade',
        'family': 'Family & Kids',
        'nature': 'Nature',
        'interior': 'Interior & Construction',
        'telegram': 'Telegram',
        'instagram': 'Instagram',
        'sales': 'Sales',
        'transport': 'Transport',
        'religion': 'Religion',
        'esoteric': 'Esoteric',
        'darknet': 'Darknet',
        'betting': 'Betting',
        'shock': 'Shock Content',
        'erotic': 'Erotic',
        'adult': 'Adults',
        'other': 'Other',
    }
}

CHATS_DIR = Path('./chats')
CHANNELS_DIR = Path('./channels')
TEMP_DIR = Path('./temp_downloads')
STATS_FILE = Path('./bot_stats.json')

MY_CHANNEL_ID = None

user_language = {}
user_state = {}


def load_stats():
    """Загрузка статистики бота"""
    if STATS_FILE.exists():
        try:
            import json
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        'total_users': set(),
        'downloads': 0,
        'active_today': set()
    }


def save_stats(stats):
    """Сохранение статистики бота"""
    try:
        import json
        stats_to_save = {
            'total_users': list(stats['total_users']),
            'downloads': stats['downloads'],
            'active_today': list(stats['active_today'])
        }
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats_to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving stats: {e}")


def update_user_stats(user_id):
    """Обновление статистики пользователя"""
    stats = load_stats()
    
    if isinstance(stats['total_users'], list):
        stats['total_users'] = set(stats['total_users'])
    if isinstance(stats['active_today'], list):
        stats['active_today'] = set(stats['active_today'])
    
    stats['total_users'].add(user_id)
    stats['active_today'].add(user_id)
    save_stats(stats)


def increment_downloads():
    """Увеличение счётчика скачиваний"""
    stats = load_stats()
    
    if isinstance(stats['total_users'], list):
        stats['total_users'] = set(stats['total_users'])
    if isinstance(stats['active_today'], list):
        stats['active_today'] = set(stats['active_today'])
    
    stats['downloads'] += 1
    save_stats(stats)


def get_text(user_id, key):
    lang = user_language.get(user_id, 'ru')
    return TEXTS[lang].get(key, '')


def ensure_dirs():
    CHATS_DIR.mkdir(exist_ok=True)
    CHANNELS_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)


def get_categories(data_type):
    directory = CHATS_DIR if data_type == 'chats' else CHANNELS_DIR
    if not directory.exists():
        return {}

    categories = {}
    for csv_file in directory.glob('*.csv'):
        filename = csv_file.stem.lower()
        if filename.startswith('tgstat_'):
            parts = filename.split('_')
            if len(parts) >= 4:
                key = parts[-1]
            else:
                key = filename[7:]
            
            try:
                df = pd.read_csv(csv_file, sep=';', encoding='utf-8-sig')
                record_count = len(df)
            except:
                record_count = 0
            
            categories[key] = {
                'file': csv_file,
                'count': record_count
            }
    return categories


def get_category_name(key, lang='ru'):
    lang_dict = CATEGORY_NAMES.get(lang, CATEGORY_NAMES['ru'])
    return lang_dict.get(key, key.title())


def csv_to_txt(csv_path, limit=None):
    try:
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')
        
        if limit and limit > 0:
            df = df.head(limit)
        
        txt_content = ""
        for idx, row in df.iterrows():
            txt_content += f"\n{'=' * 60}\nЗапись #{idx + 1}\n{'=' * 60}\n"
            for col in df.columns:
                value = row[col]
                if pd.notna(value) and str(value).strip() not in ['N/A', '']:
                    txt_content += f"{col}: {value}\n"
        
        txt_content += f"\n\n{'=' * 60}\n"
        txt_content += f"Всего записей: {len(df)}\n"
        txt_content += f"{'=' * 60}\n"
        
        return txt_content
    except Exception as e:
        print(f"Error converting CSV to TXT: {e}")
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
            
        elif format_type == 'txt':
            txt_content = csv_to_txt(src_path, limit)
            if txt_content:
                dest_path = TEMP_DIR / f"{filename}_{limit if limit else 'all'}_{timestamp}.txt"
                with open(dest_path, 'w', encoding='utf-8-sig') as f:
                    f.write(txt_content)
            else:
                return None
        
        return dest_path
    except Exception as e:
        print(f"Error copying file: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_dirs()
    user_id = update.effective_user.id
    user_language[user_id] = 'ru'
    
    update_user_stats(user_id)

    keyboard = [[
        InlineKeyboardButton('🇷🇺 Русский', callback_data='lang_ru'),
        InlineKeyboardButton('🇬🇧 English', callback_data='lang_en')
    ]]

    await update.message.reply_text(
        TEXTS['ru']['language'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats для просмотра статистики бота"""
    user_id = update.effective_user.id
    stats = load_stats()
    
    if isinstance(stats['total_users'], list):
        stats['total_users'] = set(stats['total_users'])
    if isinstance(stats['active_today'], list):
        stats['active_today'] = set(stats['active_today'])
    
    bot_info = await context.bot.get_me()
    
    channel_info = ""
    if MY_CHANNEL_ID:
        try:
            chat = await context.bot.get_chat(MY_CHANNEL_ID)
            member_count = await context.bot.get_chat_member_count(MY_CHANNEL_ID)
            channel_info = f"\n📢 Канал: {chat.title}\n👥 Подписчиков канала: <b>{member_count}</b>\n"
        except Exception as e:
            channel_info = f"\n⚠️ Не удалось получить данные канала\n💡 Добавьте бота администратором канала\n"
            print(f"Error getting channel info: {e}")
    
    stats_text = f"""📊 <b>{get_text(user_id, 'bot_stats')}</b>

👤 Имя бота: @{bot_info.username}{channel_info}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 {get_text(user_id, 'total_users')}: <b>{len(stats['total_users'])}</b>
🟢 {get_text(user_id, 'active_today')}: <b>{len(stats['active_today'])}</b>
📥 {get_text(user_id, 'total_downloads')}: <b>{stats['downloads']}</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Используйте /start для работы с ботом"""
    
    await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстового ввода количества"""
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
            
            await update.message.reply_text(
                get_text(user_id, 'select_format'),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except ValueError:
            await update.message.reply_text(get_text(user_id, 'invalid_number'))


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    await query.answer()

    if data.startswith('lang_'):
        lang = data.split('_')[1]
        user_language[user_id] = lang
        
        update_user_stats(user_id)
        
        keyboard = [[
            InlineKeyboardButton(get_text(user_id, 'chats'), callback_data='type_chats'),
            InlineKeyboardButton(get_text(user_id, 'channels'), callback_data='type_channels')
        ]]
        await query.edit_message_text(get_text(user_id, 'welcome'), reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith('type_'):
        data_type = data.split('_')[1]
        user_state[user_id] = {'type': data_type}
        categories = get_categories(data_type)

        keyboard = []
        cat_list = sorted(categories.keys())

        for i in range(0, len(cat_list), 2):
            row = []
            for j in range(2):
                if i + j < len(cat_list):
                    key = cat_list[i + j]
                    name = get_category_name(key, user_language.get(user_id, 'ru'))
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

    elif data.startswith('cat_'):
        category = data.split('_', 1)[1]
        user_state[user_id]['category'] = category
        
        categories = get_categories(user_state[user_id]['type'])
        category_count = categories.get(category, {}).get('count', 0)
        category_name = get_category_name(category, user_language.get(user_id, 'ru'))
        
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
        
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith('count_'):
        count_type = data.split('_')[1]
        
        if count_type == 'custom':
            user_state[user_id]['waiting_count'] = True
            keyboard = [[InlineKeyboardButton(get_text(user_id, 'back'), callback_data='back_to_category')]]
            await query.edit_message_text(
                get_text(user_id, 'enter_number'),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            if count_type == 'all':
                user_state[user_id]['count'] = None
            else:
                user_state[user_id]['count'] = int(count_type)
            
            keyboard = [[
                InlineKeyboardButton(get_text(user_id, 'csv'), callback_data='format_csv'),
                InlineKeyboardButton(get_text(user_id, 'txt'), callback_data='format_txt')
            ], [InlineKeyboardButton(get_text(user_id, 'back'), callback_data='back_to_count')]]
            
            await query.edit_message_text(
                get_text(user_id, 'select_format'),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    elif data.startswith('format_'):
        format_type = data.split('_')[1]
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
            except:
                pass
            
            keyboard = [[InlineKeyboardButton(get_text(user_id, 'home'), callback_data='home')]]
            success_message = f"{get_text(user_id, 'success')}\n\n📊 Выгружено записей: {count if count else src_file_data['count']}"
            await query.edit_message_text(success_message, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text(get_text(user_id, 'error'))

    elif data == 'back_to_count':
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
        
        await query.edit_message_text(
            get_text(user_id, 'select_count'),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == 'back_to_category':
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
                        name = get_category_name(key, user_language.get(user_id, 'ru'))
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

    elif data == 'back':
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
                        name = get_category_name(key, user_language.get(user_id, 'ru'))
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

    elif data == 'home':
        user_state[user_id] = {}
        keyboard = [[
            InlineKeyboardButton(get_text(user_id, 'chats'), callback_data='type_chats'),
            InlineKeyboardButton(get_text(user_id, 'channels'), callback_data='type_channels')
        ]]
        await query.edit_message_text(get_text(user_id, 'welcome'), reply_markup=InlineKeyboardMarkup(keyboard))


# Глобальная переменная для Application
bot_app: Application = None


async def setup_webhook():
    """Настройка webhook"""
    global bot_app
    
    if not WEBHOOK_URL:
        print("WARNING: WEBHOOK_URL is not set — webhook will not be installed automatically.")
        return
    
    try:
        await bot_app.bot.set_webhook(
            url=WEBHOOK_URL,
            allowed_updates=Update.ALL_TYPES
        )
        print(f"✅ Webhook установлен: {WEBHOOK_URL}")
    except Exception as e:
        print(f"❌ Ошибка установки webhook: {e}")


@app.route(f'/webhook/{TOKEN.split(":")[0]}', methods=['POST'])
def webhook():
    """Обработчик webhook от Telegram"""
    global bot_app
    
    if bot_app is None:
        return "Bot not initialized", 503
    
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot_app.bot)
        
        # Запускаем обработку в event loop
        import asyncio
        asyncio.run(bot_app.process_update(update))
        
        return "OK", 200
    except Exception as e:
        print(f"Error processing update: {e}")
        return "Error", 500


def run_flask():
    """Запуск Flask сервера"""
    app.run(host='0.0.0.0', port=PORT)


async def main():
    """Основная функция для запуска бота"""
    global bot_app
    
    # Создаём приложение бота
    bot_app = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    bot_app.add_handler(CommandHandler('start', start))
    bot_app.add_handler(CommandHandler('stats', stats_command))
    bot_app.add_handler(CallbackQueryHandler(button_callback))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    # Устанавливаем команды в меню бота
    await bot_app.bot.set_my_commands([
        BotCommand("start", "🚀 Начать работу"),
        BotCommand("stats", "📊 Статистика бота")
    ])
    
    # Инициализируем приложение
    await bot_app.initialize()
    
    # Устанавливаем webhook
    await setup_webhook()
    
    # Запускаем приложение
    await bot_app.start()
    
    print("✅ Бот запущен на Render с webhook!")
    print(f"📡 Webhook URL: {WEBHOOK_URL}")
    print(f"🌐 Port: {PORT}")
    
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Держим бота активным
    import asyncio
    while True:
        await asyncio.sleep(1)


if __name__ == '__main__':
    import asyncio
    import nest_asyncio
    
    ensure_dirs()
    
    # Для совместимости с Flask
    try:
        nest_asyncio.apply()
    except:
        pass
    
    asyncio.run(main())
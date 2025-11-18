from keep_alive import keep_alive
keep_alive()

# ----------- ВСЁ ТВОЁ (ОСТАВЛЯЮ БЕЗ ИЗМЕНЕНИЙ) -----------
import os
import shutil
import pandas as pd
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

TEXTS = {
    'ru': {
        'welcome': '🌟 Добро пожаловать в ParserTG!\n\nВыберите тип данных:',
        'chats': '💬 Чаты',
        'channels': '📢 Каналы',
        'select_category': '📁 Выберите категорию:',
        'select_format': '📋 Выберите формат:',
        'select_limit': '🔢 Сколько записей скачать?',
        'txt': '📄 TXT',
        'csv': '📊 CSV',
        'back': '⬅️ Назад',
        'home': '🏠 Главное меню',
        'language': '🌐 Выберите язык',
        'loading': '⏳ Загрузка...',
        'success': '✅ Файл готов к скачиванию!',
        'error': '❌ Ошибка',
        'no_file': '❌ Файл не найден',
        'enter_custom': '✏️ Введите число от 1 до 10000:',
        'invalid_number': '❌ Неверное число! Введите число от 1 до 10000',
        'limit_10': '10 записей',
        'limit_50': '50 записей',
        'limit_100': '100 записей',
        'limit_all': 'Все записи',
        'limit_custom': '✏️ Свое число',
        'total_records': 'Всего записей в файле: {}'
    },
    'en': {
        'welcome': '🌟 Welcome to ParserTG!\n\nSelect data type:',
        'chats': '💬 Chats',
        'channels': '📢 Channels',
        'select_category': '📁 Select category:',
        'select_format': '📋 Select format:',
        'select_limit': '🔢 How many records to download?',
        'txt': '📄 TXT',
        'csv': '📊 CSV',
        'back': '⬅️ Back',
        'home': '🏠 Home',
        'language': '🌐 Select language',
        'loading': '⏳ Loading...',
        'success': '✅ File ready for download!',
        'error': '❌ Error',
        'no_file': '❌ File not found',
        'enter_custom': '✏️ Enter number from 1 to 10000:',
        'invalid_number': '❌ Invalid number! Enter number from 1 to 10000',
        'limit_10': '10 records',
        'limit_50': '50 records',
        'limit_100': '100 records',
        'limit_all': 'All records',
        'limit_custom': '✏️ Custom number',
        'total_records': 'Total records in file: {}'
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
TOKEN = '8240135408:AAEWWO7WpWHv3qPt4hLhMZfOikiQgggjOe4'

user_language = {}
user_state = {}

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
            key = filename[7:]
            categories[key] = csv_file
    return categories

def get_category_name(key, lang='ru'):
    lang_dict = CATEGORY_NAMES.get(lang, CATEGORY_NAMES['ru'])
    return lang_dict.get(key, key.title())

def get_csv_row_count(csv_path):
    try:
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        return len(df)
    except:
        return 0

def csv_to_txt(csv_path, limit=None):
    try:
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        if limit and limit > 0:
            df = df.head(limit)
        
        txt_content = ""
        for idx, row in df.iterrows():
            txt_content += f"\n{'='*60}\nЗапись #{idx + 1}\n{'='*60}\n"
            for col in df.columns:
                value = row[col]
                if pd.notna(value) and str(value).strip() not in ['N/A', '']:
                    txt_content += f"{col}: {value}\n"
        return txt_content
    except:
        return None

def copy_file_to_temp(src_path, format_type, limit=None):
    try:
        filename = src_path.stem
        if format_type == 'csv':
            df = pd.read_csv(src_path, sep=';', encoding='utf-8')
            if limit and limit > 0:
                df = df.head(limit)
            
            dest_path = TEMP_DIR / f"{filename}_limit_{limit if limit else 'all'}.csv"
            df.to_csv(dest_path, sep=';', encoding='utf-8', index=False)
        elif format_type == 'txt':
            txt_content = csv_to_txt(src_path, limit)
            if txt_content:
                dest_path = TEMP_DIR / f"{filename}_limit_{limit if limit else 'all'}.txt"
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(txt_content)
            else:
                return None
        return dest_path
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_dirs()
    user_id = update.effective_user.id
    user_language[user_id] = 'ru'
    
    keyboard = [[
        InlineKeyboardButton('🇷🇺 Русский', callback_data='lang_ru'),
        InlineKeyboardButton('🇬🇧 English', callback_data='lang_en')
    ]]
    
    await update.message.reply_text(
        TEXTS['ru']['language'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_custom_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_state.get(user_id, {})
    
    if state.get('waiting_for_limit'):
        try:
            limit = int(update.message.text.strip())
            if 1 <= limit <= 10000:
                user_state[user_id]['limit'] = limit
                user_state[user_id]['waiting_for_limit'] = False
                
                # Получаем файл и формат
                format_type = state.get('format')
                categories = get_categories(state.get('type'))
                src_file = categories.get(state.get('category'))
                
                if not src_file:
                    await update.message.reply_text(get_text(user_id, 'no_file'))
                    return
                
                # Создаем и отправляем файл
                temp_file = copy_file_to_temp(src_file, format_type, limit)
                if temp_file and temp_file.exists():
                    with open(temp_file, 'rb') as f:
                        await update.message.reply_document(document=f, filename=temp_file.name)
                    
                    keyboard = [[InlineKeyboardButton(get_text(user_id, 'home'), callback_data='home')]]
                    await update.message.reply_text(
                        get_text(user_id, 'success'),
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    
                    # Удаляем временный файл
                    temp_file.unlink()
            else:
                await update.message.reply_text(get_text(user_id, 'invalid_number'))
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
                    row.append(InlineKeyboardButton(name, callback_data=f'cat_{key}'))
            if row:
                keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton(get_text(user_id, 'home'), callback_data='home')])
        await query.edit_message_text(get_text(user_id, 'select_category'), reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith('cat_'):
        category = data.split('_', 1)[1]
        user_state[user_id]['category'] = category
        
        keyboard = [[
            InlineKeyboardButton(get_text(user_id, 'csv'), callback_data='format_csv'),
            InlineKeyboardButton(get_text(user_id, 'txt'), callback_data='format_txt')
        ], [InlineKeyboardButton(get_text(user_id, 'back'), callback_data='back')]]
        
        await query.edit_message_text(get_text(user_id, 'select_format'), reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith('format_'):
        format_type = data.split('_')[1]
        user_state[user_id]['format'] = format_type
        
        state = user_state.get(user_id, {})
        categories = get_categories(state.get('type'))
        src_file = categories.get(state.get('category'))
        
        if not src_file:
            await query.edit_message_text(get_text(user_id, 'no_file'))
            return
        
        # Получаем количество записей в файле
        total_records = get_csv_row_count(src_file)
        
        message_text = f"{get_text(user_id, 'select_limit')}\n\n{get_text(user_id, 'total_records').format(total_records)}"
        
        keyboard = [
            [
                InlineKeyboardButton(get_text(user_id, 'limit_10'), callback_data='limit_10'),
                InlineKeyboardButton(get_text(user_id, 'limit_50'), callback_data='limit_50')
            ],
            [
                InlineKeyboardButton(get_text(user_id, 'limit_100'), callback_data='limit_100'),
                InlineKeyboardButton(get_text(user_id, 'limit_all'), callback_data='limit_all')
            ],
            [InlineKeyboardButton(get_text(user_id, 'limit_custom'), callback_data='limit_custom')],
            [InlineKeyboardButton(get_text(user_id, 'back'), callback_data='back_to_format')]
        ]
        
        await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith('limit_'):
        limit_value = data.split('_')[1]
        state = user_state.get(user_id, {})
        
        if limit_value == 'custom':
            user_state[user_id]['waiting_for_limit'] = True
            await query.edit_message_text(get_text(user_id, 'enter_custom'))
            return
        
        # Определяем лимит
        if limit_value == 'all':
            limit = None
        else:
            limit = int(limit_value)
        
        user_state[user_id]['limit'] = limit
        
        # Получаем файл
        format_type = state.get('format')
        categories = get_categories(state.get('type'))
        src_file = categories.get(state.get('category'))
        
        if not src_file:
            await query.edit_message_text(get_text(user_id, 'no_file'))
            return
        
        # Показываем загрузку
        await query.edit_message_text(get_text(user_id, 'loading'))
        
        # Создаем файл с лимитом
        temp_file = copy_file_to_temp(src_file, format_type, limit)
        if temp_file and temp_file.exists():
            with open(temp_file, 'rb') as f:
                await query.message.reply_document(document=f, filename=temp_file.name)
            keyboard = [[InlineKeyboardButton(get_text(user_id, 'home'), callback_data='home')]]
            await query.edit_message_text(get_text(user_id, 'success'), reply_markup=InlineKeyboardMarkup(keyboard))
            
            # Удаляем временный файл
            temp_file.unlink()
    
    elif data == 'back_to_format':
        category = user_state.get(user_id, {}).get('category')
        if category:
            keyboard = [[
                InlineKeyboardButton(get_text(user_id, 'csv'), callback_data='format_csv'),
                InlineKeyboardButton(get_text(user_id, 'txt'), callback_data='format_txt')
            ], [InlineKeyboardButton(get_text(user_id, 'back'), callback_data='back')]]
            
            await query.edit_message_text(get_text(user_id, 'select_format'), reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == 'back':
        data_type = user_state.get(user_id, {}).get('type')
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
                        row.append(InlineKeyboardButton(name, callback_data=f'cat_{key}'))
                if row:
                    keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton(get_text(user_id, 'home'), callback_data='home')])
            await query.edit_message_text(get_text(user_id, 'select_category'), reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == 'home':
        user_state[user_id] = {}  # Очищаем состояние
        keyboard = [[
            InlineKeyboardButton(get_text(user_id, 'chats'), callback_data='type_chats'),
            InlineKeyboardButton(get_text(user_id, 'channels'), callback_data='type_channels')
        ]]
        await query.edit_message_text(get_text(user_id, 'welcome'), reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_limit))

    print("✅ Bot started! Waiting for messages...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

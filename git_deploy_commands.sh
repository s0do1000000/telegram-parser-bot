#!/bin/bash

# Скрипт для развертывания на Render

echo "🚀 Начинаем подготовку к развертыванию на Render..."

# Проверяем Git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен!"
    exit 1
fi

# Инициализация Git (если еще не инициализирован)
if [ ! -d .git ]; then
    echo "📁 Инициализация Git репозитория..."
    git init
fi

# Добавляем все файлы
echo "📝 Добавляем файлы..."
git add .gitignore
git add .python-version
git add README.md
git add bot.py
git add requirements.txt
git add runtime.txt
git add render.yaml
git add gunicorn_config.py
git add start.sh

# Делаем директории для данных пустыми (но отслеживаемыми)
mkdir -p chats channels
touch chats/.gitkeep
touch channels/.gitkeep
git add chats/.gitkeep
git add channels/.gitkeep

# Проверяем статус
echo "📊 Статус Git:"
git status

# Коммитим изменения
echo "💾 Создаем коммит..."
git commit -m "Prepare for Render deployment

- Fixed runtime.txt and .python-version
- Updated render.yaml with all env vars
- Improved .gitignore
- Updated README.md with deployment instructions
- Added start.sh for initialization"

# Инструкции для пользователя
echo ""
echo "✅ Файлы подготовлены для коммита!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Создайте репозиторий на GitHub (если еще не создан)"
echo "2. Подключите удаленный репозиторий:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
echo ""
echo "3. Отправьте изменения:"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "4. На Render.com:"
echo "   - Создайте новый Web Service"
echo "   - Подключите ваш GitHub репозиторий"
echo "   - Render автоматически обнаружит render.yaml"
echo "   - Добавьте переменные окружения:"
echo "     * TOKEN - ваш Telegram bot token"
echo "     * WEBHOOK_URL - будет https://your-app-name.onrender.com"
echo "     * MY_CHANNEL_ID - (опционально) ID вашего канала"
echo ""
echo "5. Нажмите Deploy!"
echo ""
echo "⚠️  Важно: Загрузите CSV файлы в папки /chats и /channels"
echo "    после первого развертывания через Render Dashboard"
echo ""
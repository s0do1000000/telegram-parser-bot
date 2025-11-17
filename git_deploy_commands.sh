#!/bin/bash

# Скрипт для развертывания на Render

echo "🚀 Начинаем подготовку к развертыванию на Render..."

# Проверяем Git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен!"
    exit 1
fi

# Удаляем ненужные файлы
echo "🗑️  Удаляем ненужные файлы..."
rm -f gunicorn_config.py main

# Добавляем все файлы
echo "📝 Добавляем файлы..."
git add .gitignore
git add .python-version
git add README.md
git add bot.py
git add requirements.txt
git add runtime.txt
git add render.yaml
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
git commit -m "Fix Render deployment configuration

- Fixed render.yaml startCommand to use python bot.py
- Removed gunicorn from requirements (not needed)
- Added directory creation in buildCommand
- Updated .gitignore
- Removed unnecessary gunicorn_config.py"

echo ""
echo "✅ Файлы подготовлены!"
echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1. Отправьте изменения на GitHub:"
echo "   git push origin main"
echo ""
echo "2. На Render.com:"
echo "   - Нажмите 'Manual Deploy' → 'Clear build cache & deploy'"
echo "   - Или просто 'Manual Deploy' → 'Deploy latest commit'"
echo ""
echo "3. Установите переменные окружения (если еще не установлены):"
echo "   TOKEN = ваш_токен_от_BotFather"
echo "   WEBHOOK_URL = https://ваше-приложение.onrender.com"
echo "   MY_CHANNEL_ID = (опционально)"
echo ""
echo "4. После деплоя бот автоматически установит webhook"
echo ""
echo "⚠️  Важно: Загрузите CSV файлы в папки /chats и /channels"
echo ""
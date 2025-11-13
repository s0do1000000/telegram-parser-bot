import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application

# === ВСТАВЬ СВОЙ ТОКЕН НИЖЕ ===
TOKEN = os.getenv("TELEGRAM_TOKEN", "ВСТАВЬ_СВОЙ_ТОКЕН_СЮДА")

# Создаем Flask-приложение
app = Flask(__name__)
bot_app = Application.builder().token(TOKEN).build()

@app.route('/')
def index():
    return "Bot is running!", 200

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.update_queue.put(update)
    return "ok", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

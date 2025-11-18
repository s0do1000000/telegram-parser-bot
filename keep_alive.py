from flask import Flask
from threading import Thread
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот живой! Работает 24/7 на Replit"

def run_flask():
    try:
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        print(f"Ошибка Flask: {e}")
        time.sleep(5)  # Перезапуск через 5 сек
        run_flask()    # Рекурсивный перезапуск

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = False  # НЕ daemon — чтобы держался даже после основного потока
    t.start()
    print("Веб-сервер запущен стабильно — Replit не заснёт")

keep_alive()
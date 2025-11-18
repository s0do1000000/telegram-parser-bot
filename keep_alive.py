from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Бот живой! Работает 24/7"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# Запускаем сервер сразу при импорте
keep_alive()
print("Веб-сервер запущен — Replit не будет спать")
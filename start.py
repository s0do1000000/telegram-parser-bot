import time
import subprocess

while True:
    print("🚀 Запуск Telegram-бота...")
    process = subprocess.Popen(["python3", "main.py"])

    process.wait()   # ждём падения

    print("❌ Бот упал! Перезапуск через 3 секунды...")
    time.sleep(3)

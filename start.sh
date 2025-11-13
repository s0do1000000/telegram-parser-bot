#!/bin/bash
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 0 bot_webhook:app_flask
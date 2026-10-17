#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python -m pip install -r requirements.txt
python -m pip install gunicorn
python -m playwright install chromium
python -c 'from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(headless=True, args=["--no-sandbox"]); browser.close(); p.stop()'
python manage.py collectstatic --noinput
python manage.py migrate

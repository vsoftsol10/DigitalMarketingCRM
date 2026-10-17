#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ "${PLAYWRIGHT_BROWSERS_PATH:-}" != "0" ]]; then
    echo "Set PLAYWRIGHT_BROWSERS_PATH=0 in the Render environment for both build and runtime." >&2
    exit 1
fi

python -m pip install -r requirements.txt
python -m pip install gunicorn
python -m playwright install chromium
python -c 'import sys; from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(headless=True, args=["--no-sandbox"]); browser.close(); p.stop(); print(f"Playwright Chromium smoke check passed with {sys.executable}")'
python manage.py collectstatic --noinput
python manage.py migrate

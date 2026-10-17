#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python -m pip install -r requirements.txt
python -m pip install gunicorn
python -m playwright install --with-deps chromium
python manage.py collectstatic --noinput
python manage.py migrate

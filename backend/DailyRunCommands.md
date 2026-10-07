Terminal 1 — WSL(Redis)

sudo service redis-server start
redis-cli -a 290505 ping

Expected: PONG
---------------------------------------------------------

Terminal 2 — WSL(Celery Worker)

cd "/mnt/c/Users/S MUTHU KRISHNAN/Desktop/digital-marketing-platform/backend"
source celery-venv/bin/activate
celery -A config worker --loglevel=info
celery -A config worker --loglevel=DEBUG 2>&1 | tee celery-insights-debug.log

---------------------------------------------------------

Terminal 3 — WSL(Celery Beat)

cd "/mnt/c/Users/S MUTHU KRISHNAN/Desktop/digital-marketing-platform/backend"
source celery-venv/bin/activate
celery -A config beat --loglevel=info

---------------------------------------------------------

Terminal 4 — PowerShell(Django Backend)

cd "C:\Users\S MUTHU KRISHNAN\Desktop\digital-marketing-platform\backend"
.\venv\Scripts\Activate.ps1
python manage.py check
python manage.py runserver
python manage.py runserver_plus --cert-file localhost.crt

---------------------------------------------------------

Terminal 5 — PowerShell(React Frontend)

cd "C:\Users\S MUTHU KRISHNAN\Desktop\digital-marketing-platform\frontend"
npm run dev
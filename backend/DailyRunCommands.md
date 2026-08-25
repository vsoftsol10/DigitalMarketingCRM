Terminal 1 — WSL(Redis)

sudo service redis-server start
redis-cli -a 290505 ping

Expected: PONG
---------------------------------------------------------

Terminal 2 — WSL(Celery Worker)

cd "/mnt/c/Users/S MUTHU KRISHNAN/Desktop/digital-marketing-platform/backend"
source celery-venv/bin/activate
celery -A config worker --loglevel=info

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

---------------------------------------------------------

Terminal 5 — PowerShell(React Frontend)

cd "C:\Users\S MUTHU KRISHNAN\Desktop\digital-marketing-platform\frontend"
npm run dev
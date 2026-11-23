@echo off
REM Starts the Django API (run steps 1-3 first so outputs\signals.csv exists).
cd /d "%~dp0"
call venv\Scripts\activate
cd django_api
python manage.py migrate
python manage.py load_signals
python manage.py runserver

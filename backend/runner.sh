#!/bin/bash

python manage.py makemigrations
python manage.py migrate

python manage.py collectstatic --no-input
cp -r /app/collected_static/. /backend_static/
cp -r /app/docs/. /backend_static/

exec gunicorn --bind 0.0.0.0:8000 backend.wsgi

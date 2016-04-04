#!/bin/bash
python manage.py migrate                  # Apply database migrations
#python manage.py collectstatic --noinput  # Collect static files

# Prepare log files and start outputting logs to stdout
#touch /webapp/logs/gunicorn.log
#touch /webapp/logs/access.log
#tail -n 0 -f /webapp/logs/*.log &

# Start Gunicorn processes
#echo Starting Gunicorn.
#exec gunicorn nadine.wsgi:application \
#    --name nadine_django \
#    --bind 0.0.0.0:8000 \
#    --workers 3 \
#    --log-level=info \
#    --log-file=/webapp/logs/gunicorn.log \
#    --access-logfile=/webapp/logs/access.log \
#    "$@"

python manage.py runserver 0.0.0.0:8000

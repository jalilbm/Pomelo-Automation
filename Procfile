web: gunicorn pomelo.wsgi
worker: celery -A pomelo worker --loglevel=info -Q handle_messages_activation_queue -c 1
beat: celery -A pomelo beat --loglevel=info
celery -A celery_app.celery worker --loglevel info -P gevent --autoscale 8,16
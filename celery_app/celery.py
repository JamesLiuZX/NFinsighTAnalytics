from celery.app import Celery
from time import sleep

broker_url = "amqp://localhost"
redis_url = "redis://localhost"

app = Celery(__name__, broker=broker_url, backend=redis_url)

@app.task
def say_hello(name: str):
    sleep(5)
    return f'hello {name}'
# NFInsight Analytics

This is the repo for NFInsight's ETL and Analytics server.

To run, simply follow these steps:

1. Clone the repo.
2. Create a virtual environment within the directory. We recommend using Python 3.10.
3. Activate the virtual environment.
4. Grab your database connection strings and populate it in a `.env` file in the `/app` folder.
    - You may use the `.env.example` as a guideline.
    - You should also generate an app secret for authenticating JWT tokens.

5. Run these commands:

```shell
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The server should be up and running. To visit the OpenAPI spec, simply go to `127.0.0.1:8000/docs` in your browser.

Developed by @SeeuSim and @JamesLiuZX

## Celery Demo

If you're wondering what Celery is, it is a backend tasks broker that can be used to run background tasks.

We've configured Celery in this project to use a RabbitMQ broker with py-amqp, and a Redis in-memory results backend that can be used for an access lock if needed.

Here's how to run the demo:

1. If you haven't already, activate your virtual environment for python, and install the `requirements.txt` as described above.
2. Ensure that your system has Docker installed, and that the Docker daemon is up and running. In OSes with GUI, you may simply launch the Docker Desktop client.
3. Run this command in your terminal:

```sh
docker-compose up
```

As per our docker config, this will spin up a docker container that has both a RabbitMQ message queue and a Redis in-memory database.
4. Run the command `celery -A app.celery worker -l info --pool=solo`. This should spin up your celery server.
5. Now, your app may call any function denoted with `@app.task` in `app/celery.py`. This should run in the background.
6. To illustrate, open a separate shell with the same venv activated, and run this:

```sh
python3

>> from app.celery import say_hello
>> say_hello.delay("your_name")
```

You should be able to see the Celery worker handle and execute the task. In the future, we hope to be able to implement the necessary APIs to manage, start and stop tasks.

Remember to run `docker-compose down` to stop your Docker container when you're done.

## Upcoming Features

1. Authenticated route to trigger jobs
2. Training Scripts
3. ETL Scripts
4. Cassandra integration with Cosmos
5. Worker jobs
6. Docker File
7. CI to build and deploy to ACA

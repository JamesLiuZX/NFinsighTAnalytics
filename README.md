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
# Install requirements
python -m pip install -r requirements.txt

# Add execute permissions for the script
chmod +x ./scripts/api.sh

# Run the app
./scripts/api.sh # OR uvicorn fastapi_app.main:app --reload
```

The server should be up and running. To visit the OpenAPI spec, simply go to `127.0.0.1:8000/docs` in your browser.

Developed by @SeeuSim and @JamesLiuZX

## Database Introspection

The Python ORM by DataStax has some flaws. Hence, we execute our queries using only its raw CQL execution engine.

To connect to the database, run the following in your terminal, using Docker:

```sh
docker run -it --rm -e SSL_VALIDATE=false -e SSL_VERSION=TLSv1_2 cassandra:3.11 cqlsh \
  <database_account_name>.cassandra.cosmos.azure.com 10350 \
  -u <database_user> \
  -p <database_password> \
  -k <database_keyspace_name> --ssl
```

Thereafter, you should be able to test and execute queries using [`CQL`](https://cassandra.apache.org/doc/latest/cassandra/cql/index.html).

Once your queries have been validated, use `session.prepare` and `session.execute` in your Python code to execute database statements.

## Celery Demo

If you're wondering what Celery is, it is a backend tasks broker that can be used to run background tasks.

We've configured Celery in this project to use a RabbitMQ broker with py-amqp, and a Redis in-memory results backend that can be used for an access lock if needed.

Here's how to run the demo:

1. If you haven't already, activate your virtual environment for python, and install the `requirements.txt` as described above.
2. Ensure that your system has:
  
  - Docker installed, and that the Docker daemon is up and running. In OSes with GUI, you may simply launch the Docker Desktop client.
  - `minikube` installed
  - `kubectl` installed

3. Ensure all your environment variables are set. You may follow the respective `.env.example` files.
4. Run this command in your terminal:

```sh
# Start the containers for the message broker and results backend
minikube start
kubectl apply -f k8s_conf.yaml
minikube tunnel
```

As per our kubernetes config, this will spin up a control plane that has both a RabbitMQ message queue and a Redis in-memory database. 

The tunnel mirrors the load balancing services so that the ports are natively accessible on `localhost`.

5. In a new terminal, run the script `./scripts/celery.sh`. This should spin up your celery server.
6. Now, your app may call any function denoted with `@app.task` in `app/celery.py`. This should run in the background.
7. To illustrate, open a separate shell with the same venv activated, and run this:

```sh
# Start a REPL environment for testing
python3

>> from celery_app.celery import create_collection
>> create_collection.delay("your_name")
```

You should be able to see the Celery worker handle and execute the task. In the future, we hope to be able to implement the necessary APIs to manage, start and stop tasks.

8. You may also run the script `./scripts/flower.sh` in another terminal to see a GUI to view task running statuses at `localhost:5556`. Remember to run the same chmod command on the flower script. Alternatively, you can run 
`find ./scripts -type f -exec chmod +x {} +` 
to enable permissions for all current script files within the folder. 

9. To spin down the celery app and related resources, perform these actions in this sequence:

  - Terminate the flower script by running <kbd>Cmd+C</kbd> in the `flower.sh` terminal.
  - Terminate the celery script by running <kbd>Cmd+C</kbd> in the `celery.sh` terminal.
  - Terminate the Kubernetes resources by running `kubectl delete -f k8s_conf.yaml`.
  

## Upcoming Features

1. Authenticated route to trigger jobs
2. Training Scripts
3. ETL Scripts
4. Cassandra integration with Cosmos
5. Worker jobs
6. Docker File
7. CI to build and deploy to ACA

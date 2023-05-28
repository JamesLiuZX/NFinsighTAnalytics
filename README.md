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
chmod +x ./scripts/api.sh`

# Run the app
./scripts/api.sh # OR uvicorn fastapi_app.main:app --reload
```

The server should be up and running. To visit the OpenAPI spec, simply go to `127.0.0.1:8000/docs` in your browser.

Developed by @SeeuSim and @JamesLiuZX

## Celery Demo

If you're wondering what Celery is, it is a backend tasks broker that can be used to run background tasks.

We've configured Celery in this project to use a RabbitMQ broker with py-amqp, and a Redis in-memory results backend that can be used for an access lock if needed.

Here's how to run the demo:

1. If you haven't already, activate your virtual environment for python, and install the `requirements.txt` as described above.
2. Ensure that your system has Docker installed, and that the Docker daemon is up and running. In OSes with GUI, you may simply launch the Docker Desktop client.
3. Ensure all your environment variables are set. Most importantly, this:

  - `EVENTLET_HUB=poll`. To check this, run `echo $EVENTLET_HUB`

4. Run this command in your terminal:

```sh
# Start the containers for the message broker and results backend
docker-compose up
```

As per our docker config, this will spin up a docker container that has both a RabbitMQ message queue and a Redis in-memory database.

5. In a new terminal, run the script `./scripts/celery.sh`. This should spin up your celery server.
6. Now, your app may call any function denoted with `@app.task` in `app/celery.py`. This should run in the background.
7. To illustrate, open a separate shell with the same venv activated, and run this:

```sh
# Start a REPL environment for testing
python3

>> from celery_app.celery import say_hello
>> say_hello.delay("your_name")
```

You should be able to see the Celery worker handle and execute the task. In the future, we hope to be able to implement the necessary APIs to manage, start and stop tasks.

8. You may also run the script `./scripts/flower.sh` in another terminal to see a GUI to view task running statuses at `localhost:5556`.

9. To spin down the celery app and related resources, perform these actions in this sequence:

  - Terminate the flower script by running <kbd>Cmd+C</kbd> in the `flower.sh` terminal.
  - Terminate the celery script by running <kbd>Cmd+C</kbd> in the `celery.sh` terminal.
  - Terminate the Docker resources by running <kbd>Cmd+C</kbd> in the `docker-compose` terminal.
  
Alternatively, you can run `docker-compose down` from another terminal to stop your Docker containers when you're done.

## Testing kubernetes

To start, ensure you have the following:

- Docker Desktop
  - Ensure that you have at least 2 CPU cores enabled for minikube to run.
- minikube
- kubectl

1. Launch the Docker daemon/desktop app and run `minikube start`.
2. Run `kubectl apply -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"`
3. Run `kubectl apply -f k8s_deployment.yml`. This will apply the cluster settings and start a Kubernetes cluster with the RabbitMQ server(s).
4. To get the default credentials, run the following:

```sh
username="$(kubectl get secret rabbitmq-default-user -o jsonpath='{.data.username}' | base64 --decode)"
echo "username: $username"
password="$(kubectl get secret rabbitmq-default-user -o jsonpath='{.data.password}' | base64 --decode)"
echo "password: $password"
```

5. Expose the management UI.

```sh
# Forward the ports to the current machine
kubectl -n nf-etl port-forward service/rabbitmq 15672
```

To ensure best results, use Chrome or Safari to view the webpage at `http://localhost:15672`.

6. You may also expose the AMQP message queue server at port `5672` in a similar fashion.
7. Once done, close all connections and run the following:

```sh
kubectl -n nf-etl delete pod,statefulset,svc --all # Terminate all nodes and services within the namespace.

minikube stop #Stop the docker server running Kubernetes
```

8. Due to small scale and infrastructure costs, Kubernetes is not as practical as Docker-Compose for now. In the future, when scale increases, we will migrate over.


## Upcoming Features

1. Authenticated route to trigger jobs
2. Training Scripts
3. ETL Scripts
4. Cassandra integration with Cosmos
5. Worker jobs
6. Docker File
7. CI to build and deploy to ACA

# NFInsight Analytics

This is the repo for NFInsight's ETL server.

![image](https://github.com/SeeuSim/nfinsight_analytics/assets/90857020/17e95414-4c12-4442-93d5-ccdbcc395e05)

This repo consists of the Docker application code needed to run the ETL layer, in the above diagram. 

In the future, we hope to incorporate some analytics workflows with these Cassandra clusters, and with Tensorflow and Spark.

Developed by [@SeeuSim](https://github.com/SeeuSim) and [@JamesLiuZx](https://github.com/JamesLiuZX)

## Set up

To run, simply follow these steps:

1. Clone the repo.
2. Create a virtual environment within the directory. We recommend using Python 3.10.
3. Activate the virtual environment.
4. Grab your API connection strings and populate it in a `.env` file in the `/etl/fastapi_app` folder.
    - You may use the `.env.example` as a guideline.
    - You should also generate an app secret for authenticating JWT tokens.

Additional care needs to be taken when setting up the database. Please refer to `etl/database.py`:

- For Datastax Astra: (You may also refer to [Astra set up](#astra-set-up-on-local))
  - It uses a zip file which we store the in `etl` folder that is referenced in `etl/database.py`. To get this package,
    go to your Datastax Astra console and grab the "connection bundle" and save it in the `etl` folder.
  - For its other variables, populate them according the the `etl/.env.example` file.
- For Azure Cosmos:
  - The code in `database.py` will need to be modified, as well as the environment variables needed.
  - This applies for other Cassandra clusters as well.

5. Using your Cassandra CQL shell, create all the tables in the `etl/celery_app/db/models.py` with those commands.

6. Insert an admin user with username and bcrypt hashed password into the `admin_user` table.

7. Run these commands:

```shell
# Build the app from the local code.
docker compose up --build
```

The server should be up and running. To visit the OpenAPI spec, simply go to `127.0.0.1/docs` in your browser.

8. To trigger authenticated routes, key in the credentials from step 6 and click `authenticate` in the OpenAPI spec,

9. To spin down the server, simply run <kbd>Cmd + C</kbd> in the Docker Compose terminal.


### Astra set up on local

You first need to create a Datastax Astra database, and navigate to your database admin console on the web.

To set up, simply download your `secure-connect-{database_name}` bundle and populate it in the `etl` folder.
Reference that (including the database name) in the `etl/database.py` file by setting the variables in the `etl/.env` file:

```sh
ASTRA_DB_NAME="<value>"
ASTRA_CLIENT_ID="<value>"
ASTRA_CLIENT_SECRET="<value>"
ASTRA_TOKEN="<value>"

ASTRA_KEYSPACE="<keyspace>"
```

These values can be obtained from your Astra DB web console.

### Database Introspection

The Python ORM by DataStax has some flaws. Hence, we execute our queries using only its raw CQL execution engine.

To connect to the database, create a [Datastax Astra](https://www.datastax.com/products/datastax-astra) account and database, and use either their web CQL shell or execute
raw queries with its various drivers.

Within the web shell, you should be able to test and execute queries using [`CQL`](https://cassandra.apache.org/doc/latest/cassandra/cql/index.html).

Once your queries have been validated, use `session.prepare` and `session.execute` in your Python code to execute database statements.

### CQL Injection

Within our code, there are multiple CQL injection vulnerabilities with raw f-string queries. However, as we are not storing sensitive data
within the database and are optimising our queries for batch performance, we will leave them as such for now.

Fixes proposed are welcome, via our [issues](https://github.com/SeeuSim/NFinsighTAnalytics/issues) section.

## Celery Demo

If you're wondering what Celery is, it is a backend tasks broker that can be used to run background tasks.

We've configured Celery in this project to use a RabbitMQ broker with py-amqp, and a Redis in-memory results backend that can be used for an access lock if needed.

Here's how to run the demo:

1. If you haven't already, ensure that your system has:

  - Docker installed, and that the Docker daemon is up and running. In OSes with GUI, you may simply launch the Docker Desktop client.

2. Ensure all your environment variables are set. You may follow the respective `.env.example` files.
3. Run this command in your terminal:

```sh
docker-compose up
```

4. Now, your app may call any function denoted with `@app.task` in `app/celery.py`. This should run in the background.
5. To illustrate, open a separate shell with the same venv activated, and run this:

```sh
# Start a REPL environment for testing
python3

>> from celery_app.celery import app
>> app.send_task('task_name', args=(...), kwargs={...})
```

You should be able to see the Celery worker handle and execute the task. In the future, we hope to be able to implement the necessary APIs to manage, start and stop tasks.

6. You may also run the script `./scripts/flower.sh` in another terminal to see a GUI to view task running statuses at `localhost:5556`.
  Remember to run the same chmod command on the flower script. Alternatively, you can run 
  `find ./scripts -type f -exec chmod +x {} +` 
  to enable permissions for all current script files within the folder. 

7. To spin down the celery app and related resources, perform these actions in this sequence:

  - Terminate the flower script by running <kbd>Cmd+C</kbd> in the `flower.sh` terminal.
  - Terminate the containers by running `docker-compose down` from another terminal.
  
## Kubernetes

If Kubernetes is more your thing, we also provide a set up for kubernetes.

We also provide a Kubernetes workflow under `k8s/Setup.md`.

**Pre-requisites:** Modify the kubernetes scripts image tags for the celery deployment and the fastapi deployment to point to your local images that were previously built with docker compose.

They may be found under: `./k8s/resources/celery-worker-deployment.yaml` and `./k8s/resources/fastapi-application-deployment.yaml`.

1. Ensure that you have `minikube` and `kubectl` on your system.
2. Ensure that the Docker daemon is running.
3. Run the commands below:

```sh
#Start the local control plane with minikube
minikube start

# Create the necessary namespaces
kubectl apply -f k8s/namespace.yaml

# Create the resources
kubectl apply -f k8as/resources

# Mirror the ports
minikube tunnel
```

Now, you will be able to interact with the containers and the FastAPI application as if you were running docker-compose. To terminate, simply run `kubectl delete -f k8s/resources`.

NOTE: Do NOT delete the namespace.

## Upcoming Features

1. Model Training Scripts
2. CI to build and deploy to ACA

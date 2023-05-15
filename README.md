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

## Upcoming Features

1. Authenticated route to trigger jobs
2. Training Scripts
3. ETL Scripts
4. Cassandra integration with Cosmos
5. Worker jobs
6. Docker File
7. CI to build and deploy to ACA

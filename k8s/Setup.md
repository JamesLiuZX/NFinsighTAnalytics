# Set up

To setup, there are a few steps to follow. We recommend that you follow the instructions in each following section, in sequence.

## 1. Building and pushing to Github Container Registry

First, build all the requisite images and test that they work locally with Docker-Compose:

```sh
# dir: ./
docker-compose up --build
```

Once all the behaviors have been verified, you may proceed to the next step.

## 2. Tagging and pushing to GHCR

Follow these steps to push the images to GHCR.

1. Get a [PAT](https://github.com/settings/tokens) from Github, and enable the relevant permissions.

2. Test the log in.

```sh
echo $PAT | docker login ghcr.io -u {username}--password-stdin

# $ Login Succeeded
```

3. Push the image to GHCR.

```sh
# Set Variables
export USERNAME={USERNAME}
export REPO={REPO}
export VERSION={VERSION}

# Tag the celery image
docker tag nf_etl_celery ghcr.io/$USERNAME/$REPO/nf_etl_celery:$VERSION

# Tag the fastapi image
docker tag nf_etl_api ghcr.io/$USERNAME/$REPO/nf_etl_api:$VERSION

# push the images to GHCR
docker push ghcr.io/$USERNAME/$REPO/nf_etl_celery:$VERSION
docker push ghcr.io/$USERNAME/$REPO/nf_etl_api:$VERSION
```

4. You may inspect the container images.

```sh
#CELERY
docker inspect ghcr.io/$USERNAME/$REPO/nf_etl_celery:$VERSION

#API
docker inspect ghcr.io/$USERNAME/$REPO/nf_etl_api:$VERSION
```

## Configure secret for K8s namespace

1. If you haven't already, create the namesace with this command:

```sh
kubectl apply -f namespace.yaml
```

2. Create the secret for the namespace with the PAT obtained earlier.

```sh
kubectl -n nf-etl create secret docker-registry ghcr-login-secret \
  --docker-server=https://ghcr.io \
  --docker-username=<username> \
  --docker-password=<PAT> \
  --docker-email=<email>
```

## Start the applications

1. Run this command (in the `k8s` folder):

```sh
kubectl apply -f ./resources
```

2. To mirror the ports onto your local machine, run this command:

```sh
minikube tunnel
```

3. Visit the API server at `http://localhost/docs`. You may execute the APIs via the Swagger UI.

4. To inspect the logs, you may run these commands:

```sh
# CELERY
kubectl -n nf-etl logs -f pod/$(kubectl -n nf-etl get pod | grep celery | awk '{print $1}')

# API
kubectl -n nf-etl logs -f pod/$(kubectl -n nf-etl get pod | grep fastapi | awk '{print $1}')
```

Run <kbd>Cmd + C</kbd> to exit the logs session.

5. To SSH into the containers, you may run these commands:

```sh
# CELERY
kubectl -n nf-etl exec -it pod/$(kubectl -n nf-etl get pod | grep celery | awk '{print $1}') -- /bin/sh

# API
kubectl -n nf-etl logs -it pod/$(kubectl -n nf-etl get pod | grep fastapi | awk '{print $1}') -- /bin/sh
```

Run <kbd>Cmd + D</kbd> to exit the SSH session.

6. When done, stop the minikube tunnel with <kbd>Cmd + C</kbd>

7. Next, run this command in the `k8s` container:

```sh
kubectl delete -f ./resources
```

8. Do NOT delete the namespace (else you'll have to re-setup the Secret)

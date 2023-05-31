# Kubernetes, with Helm

Here's how to create and interact with the servers, namely Redis and RabbitMQ.

1. Run `start.sh`. This will start all the services.
2. Run `kubectl port-forward service/rabbitmq 15672`. This will allow you to view the UI.
3. Run `kubectl port-forward service/rabbmitmq 5672`. This will allow you to access the queue via AMQP.
4. Run `kubectl port-forward service/redis 6379`. This will allow you to access the Redis store.

Run `kubectl get all` to verify that all services have been set up. This sets up mainly:
  
  - A Deployment, for each of the RabbitMQ and Redis services.
    - A Pod, for each of the services
    - A Claim for persistent storage, for:
      - RabbitMQ logs
      - RabbitMQ data
      - Redis data
    - A Service, for each of the services
    - A Replicaset, for each of the services to ensure graceful restarts in the event of failure.

5. When done, run `stop.sh`. If it lags, execute <kbd>Cmd + C</kbd> to proceed to the next teardown step.
6. Run `kubectl get all` to verify that all services are indeed torn down.

---

**This chart was created by Kompose**

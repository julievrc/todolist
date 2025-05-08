# Kubernetes Deployment Guide

This guide will help you deploy the Todo List application to Kubernetes.

## Prerequisites

- Docker installed
- kubectl configured to connect to your Kubernetes cluster
- Access to a Google Container Registry (gcr.io)

## Step 1: Build and Push Docker Images

Build and push the Docker images to Google Container Registry:

```bash
# Build the frontend image
docker build -t gcr.io/trusty-shine-453002-b9/todolist:latest -f Dockerfile .

# Build the API image
docker build -t gcr.io/trusty-shine-453002-b9/todolist-api:latest -f Dockerfile.api .

# Push the images to Google Container Registry
docker push gcr.io/trusty-shine-453002-b9/todolist:latest
docker push gcr.io/trusty-shine-453002-b9/todolist-api:latest
```

## Step 2: Create Kubernetes Secrets

Run the script to create necessary Kubernetes secrets:

```bash
./k8s/create-secrets.sh
```

## Step 3: Deploy MySQL Database

Deploy the MySQL database:

```bash
kubectl apply -f k8s/mysql-deployment.yaml
```

Wait for MySQL to be ready:

```bash
kubectl get pods -l app=mysql
```

## Step 4: Deploy API Backend

Deploy the API backend:

```bash
kubectl apply -f k8s/api-deployment.yaml
```

Wait for the API to be ready:

```bash
kubectl get pods -l app=todo-api
```

## Step 5: Deploy Frontend

Deploy the frontend:

```bash
kubectl apply -f k8s/frontend-deployment.yaml
```

Wait for the frontend to be ready:

```bash
kubectl get pods -l app=todo-frontend
```

## Step 6: Access the Application

If you're using minikube, you can use port-forwarding to access the frontend:

```bash
kubectl port-forward svc/todo-frontend 8080:80
```

Then visit http://localhost:8080 in your browser.

If you're using an ingress controller, wait for the ingress to get an IP address:

```bash
kubectl get ingress todo-ingress
```

Then visit the IP address in your browser.

## Troubleshooting

If pods are not starting properly, check the logs:

```bash
# Check API logs
kubectl logs -l app=todo-api

# Check frontend logs
kubectl logs -l app=todo-frontend

# Check MySQL logs
kubectl logs -l app=mysql
```

For more detailed status:

```bash
kubectl describe pod <pod-name>
```

### Common Issues and Solutions

#### MySQL Pod Stuck in Pending State

If your MySQL pod is stuck in the "Pending" state with a message about unbound PersistentVolumeClaims:

```bash
kubectl delete -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/mysql-deployment.yaml
```

This issue is fixed in the latest version of the deployment files, which creates a PersistentVolume using hostPath storage.

#### API or Frontend Pods Crashing

If your API or frontend pods are crashing, check if the secrets were created correctly:

```bash
kubectl get secrets
```

Make sure `google-translate-creds` and `api-secrets` exist. If not, run the create-secrets.sh script:

```bash
cd k8s && ./create-secrets.sh
```

#### Liveness or Readiness Probe Failures

If pods are restarting due to liveness or readiness probe failures:

1. Check the pod logs to see if the application is running properly
2. Make sure the health endpoints are implemented in your code
3. You may need to adjust the initialDelaySeconds in the probe configuration if your app takes longer to start

## Clean Up

To delete all resources:

```bash
kubectl delete -f k8s/frontend-deployment.yaml
kubectl delete -f k8s/api-deployment.yaml
kubectl delete -f k8s/mysql-deployment.yaml
kubectl delete secret google-translate-creds
kubectl delete secret api-secrets
kubectl delete secret mysql-secrets
```
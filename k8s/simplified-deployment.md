# Simplified Kubernetes Deployment Guide

This guide provides a simplified approach to deploy your Todo List application on Kubernetes.

## Step 1: Build and Push Docker Images

You need to build and push your Docker images to your Google Container Registry:

```bash
# Navigate to your project directory
cd /Users/juliettevanravenswaayclaasen/Documents/sync-docs/School/Spring\ 2025/cloud\ computing/final-project\ copy/todolist/

# Build the frontend image
docker build -t gcr.io/trusty-shine-453002-b9/todolist:latest -f Dockerfile .

# Build the API image
docker build -t gcr.io/trusty-shine-453002-b9/todolist-api:latest -f Dockerfile.api .

# Push the images to Google Container Registry
# First, authenticate with Google Cloud (you may need to install gcloud CLI)
gcloud auth configure-docker

# Then push the images
docker push gcr.io/trusty-shine-453002-b9/todolist:latest
docker push gcr.io/trusty-shine-453002-b9/todolist-api:latest
```

## Step 2: Create Kubernetes Secrets

Create the necessary secrets:

```bash
# Create API secret
kubectl create secret generic api-secrets --from-literal=secret-key=your_secure_secret_key

# Create Google credentials secret
kubectl create secret generic google-translate-creds --from-file=google-credentials.json=./k8s/trusty-shine-453002-b9-b9ba8ba27281.json
```

## Step 3: Apply MySQL Deployment

```bash
kubectl apply -f k8s/mysql-deployment.yaml
```

Wait for MySQL to be ready:

```bash
kubectl get pods -l app=mysql
```

## Step 4: Apply API and Frontend Deployments

```bash
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

## Step 5: Check Deployment Status

```bash
kubectl get pods
```

## Step 6: Access Your Application

If you're using a Load Balancer or Ingress:

```bash
kubectl get svc todo-frontend
# or
kubectl get ingress todo-ingress
```

## Troubleshooting

### Common Issues:

1. **Image Pull Failures**:
   - Ensure you've built and pushed your Docker images to the correct registry
   - Verify you have the necessary permissions to pull from the registry

2. **Resource Constraints**:
   - If pods remain in Pending state due to resource constraints, update the resource limits in the deployment files
   - You may need to increase the size of your cluster nodes

3. **MySQL Connection Issues**:
   - Verify MySQL is running: `kubectl logs -l app=mysql`
   - Check environment variables in the API deployment

4. **Persistent Volume Issues**:
   - GKE should automatically provision PVs, but if there are issues, you can use a simpler approach without PVs

### Additional Commands:

```bash
# View pod logs
kubectl logs <pod-name>

# Describe a pod for detailed information
kubectl describe pod <pod-name>

# Exec into a pod for debugging
kubectl exec -it <pod-name> -- sh
```

## Cleanup

To delete all Kubernetes resources:

```bash
kubectl delete -f k8s/frontend-deployment.yaml
kubectl delete -f k8s/api-deployment.yaml
kubectl delete -f k8s/mysql-deployment.yaml
kubectl delete secret google-translate-creds
kubectl delete secret api-secrets
```
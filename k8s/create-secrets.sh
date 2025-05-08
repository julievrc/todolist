#!/bin/bash

# Set the current directory to the script's directory
cd "$(dirname "$0")"

# Display current working directory for debugging
echo "Current directory: $(pwd)"
echo "Checking if credentials file exists..."

# First look for the standardized google-credentials.json file
CREDENTIALS_FILE=""

if [ -f "../google-credentials.json" ]; then
  echo "Credentials file found at ../google-credentials.json"
  CREDENTIALS_FILE="../google-credentials.json"
elif [ -f "trusty-shine-453002-b9-b9ba8ba27281.json" ]; then
  echo "Credentials file found at trusty-shine-453002-b9-b9ba8ba27281.json"
  CREDENTIALS_FILE="trusty-shine-453002-b9-b9ba8ba27281.json"
else
  echo "Credentials file not found in $(pwd)"
  echo "Searching for credentials file..."
  
  # Look for any JSON files that might be credentials
  FOUND_FILES=$(find .. -name "*.json" -not -path "*/node_modules/*" 2>/dev/null)
  
  if [ -z "$FOUND_FILES" ]; then
    echo "Error: No Google credentials file found. Please make sure it exists."
    echo "Create a service account key in Google Cloud and save it as google-credentials.json in the project root."
    exit 1
  else
    echo "Found potential credential files:"
    echo "$FOUND_FILES"
    echo "Please specify which file to use or rename your credentials file to google-credentials.json"
    exit 1
  fi
fi

# Create the Google Cloud credentials secret
echo "Creating Google Cloud credentials secret..."
kubectl create secret generic google-translate-creds \
  --from-file=google-credentials.json=$CREDENTIALS_FILE

# Create API secrets
echo "Creating API secrets..."
kubectl create secret generic api-secrets \
  --from-literal=secret-key=your_secure_secret_key

# Create MySQL secrets
echo "Creating MySQL secrets..."
kubectl create secret generic mysql-secrets \
  --from-literal=root-password=rootpassword \
  --from-literal=user-password=todopassword

echo "Kubernetes secrets created successfully!"
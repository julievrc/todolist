#!/bin/bash

# Config
INSTANCE_NAME="flask-todo"
ZONE="us-east1-d"
PROJECT_ID=$(gcloud config get-value project)

# 1. Create the VM
gcloud compute instances create "$INSTANCE_NAME" \
    --zone="$ZONE" \
    --machine-type=e2-micro \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --tags=http-server \
    --metadata=startup-script='#!/bin/bash
      apt update
      apt install -y python3-venv
      mkdir /home/jhv/Homework3
      cd /home/jhv/Homework3
      python3 -m venv venv
      source venv/bin/activate
      pip install flask'

# 2. Wait for the VM to be ready
echo "Waiting 30 seconds for VM to finish startup tasks..."
sleep 30

# 3. Upload your app folder
gcloud compute scp --recurse ~/Homework3 jhv@"$INSTANCE_NAME":~ --zone="$ZONE"

# 4. Run the app
gcloud compute ssh jhv@"$INSTANCE_NAME" --zone="$ZONE" --command="
  cd Homework3
  sudo venv/bin/python todolist.py &
"

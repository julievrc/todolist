# AWS EC2 Deployment Guide for Todo List Application

This guide provides step-by-step instructions for deploying the Todo List application on AWS EC2 as part of a multi-cloud strategy.

## Prerequisites

1. AWS account with access to EC2, VPC, and Security Groups
2. AWS CLI installed and configured
3. Docker and Docker Compose installed on your local machine
4. Google Cloud service account key for Translate API

## Step 1: Create EC2 Instance

1. Log in to the AWS Management Console
2. Navigate to EC2 Dashboard
3. Click "Launch Instance"
4. Configure the instance:
   - **Name**: todo-app
   - **AMI**: Amazon Linux 2023
   - **Instance Type**: t2.micro (Free tier eligible)
   - **Key Pair**: Create a new key pair or use an existing one
   - **VPC and Subnet**: Use default or select specific ones
   - **Auto-assign Public IP**: Enable
   - **Security Group**: Create a new security group with the following rules:
     - SSH (22): Your IP
     - HTTP (80): Anywhere
     - HTTPS (443): Anywhere
     - Custom TCP (5001): Anywhere (for API access)
5. Click "Launch Instance"

## Step 2: Connect to the EC2 Instance

```bash
# Download and use your key pair
chmod 400 your-key.pem
ssh -i your-key.pem ec2-user@your-instance-public-ip
```

## Step 3: Install Required Software

```bash
# Update the system
sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and log back in for group changes to take effect
exit
# Log back in
ssh -i your-key.pem ec2-user@your-instance-public-ip

# Verify installations
docker --version
docker-compose --version
```

## Step 4: Set Up Application

```bash
# Create application directory
mkdir -p ~/todo-app
cd ~/todo-app

# Copy application files to the EC2 instance
# On your local machine, run:
scp -i your-key.pem -r /path/to/your/local/app/* ec2-user@your-instance-public-ip:~/todo-app/

# Back on the EC2 instance:
# Create a Google credentials file
nano ~/todo-app/google-credentials.json
# Paste your Google Cloud service account key JSON
```

## Step 5: Configure the Application

```bash
# Edit the docker-compose.yml if needed
nano ~/todo-app/docker-compose.yml

# Modify environment variables as needed
```

## Step 6: Deploy the Application

```bash
# Start the application
cd ~/todo-app
docker-compose up -d

# Verify the containers are running
docker-compose ps
```

## Step 7: Set up SSL with Certbot (Optional but Recommended)

```bash
# Install Certbot
sudo amazon-linux-extras install epel -y
sudo yum install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Certbot will automatically configure Nginx for SSL
```

## Step 8: Set Up Auto-Renewal for SSL Certificate

```bash
# Test certificate renewal
sudo certbot renew --dry-run

# Add a cron job to automatically renew certificates
echo "0 3 * * * root certbot renew --quiet" | sudo tee -a /etc/crontab
```

## Step 9: Configure Automated Backups

```bash
# Create a script to backup the MySQL data
cat > ~/backup.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/home/ec2-user/backups"
mkdir -p $BACKUP_DIR

# Backup MySQL database
docker exec todo-app_mysql_1 mysqldump -u todouser -ptodopassword tododb > $BACKUP_DIR/db_backup_$TIMESTAMP.sql

# Compress the backup
gzip $BACKUP_DIR/db_backup_$TIMESTAMP.sql

# Remove backups older than 7 days
find $BACKUP_DIR -type f -name "db_backup_*.sql.gz" -mtime +7 -exec rm {} \;
EOF

# Make the script executable
chmod +x ~/backup.sh

# Schedule daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ec2-user/backup.sh") | crontab -
```

## Step 10: Set Up Monitoring (Optional)

```bash
# Install CloudWatch agent
sudo yum install -y amazon-cloudwatch-agent

# Configure CloudWatch agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard

# Start CloudWatch agent
sudo systemctl enable amazon-cloudwatch-agent
sudo systemctl start amazon-cloudwatch-agent
```

## Step 11: Access Your Application

Your application should now be running and accessible at:

- Frontend: http://your-instance-public-ip
- API: http://your-instance-public-ip:5001

If you configured a domain and SSL, use:
- https://yourdomain.com

## Troubleshooting

### Check container logs
```bash
docker-compose logs -f
```

### Check specific container logs
```bash
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f mysql
```

### Restart the application
```bash
docker-compose restart
```

### Rebuild and restart the application
```bash
docker-compose down
docker-compose up -d --build
```

## Multi-Cloud Integration

This AWS EC2 deployment can work alongside your Google Cloud Kubernetes deployment by:

1. **API Gateway**: Set up an API Gateway to route traffic between AWS and GCP
2. **DNS Load Balancing**: Configure Route 53 to distribute traffic between clouds
3. **Database Replication**: Implement MySQL replication for data consistency
4. **Shared Storage**: Use a cloud storage solution accessible from both platforms

For detailed multi-cloud setup, refer to the `multi-cloud-integration.md` document.
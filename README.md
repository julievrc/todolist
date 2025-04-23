# Enhanced Todo List Application

A full-stack Todo List application with advanced features, deployed across multiple cloud providers. This project demonstrates modern cloud-native development practices and multi-cloud deployment strategies.

## Features

### User Management
- User registration and login with JWT authentication
- Secure password storage with hashing
- User-specific task lists

### Task Management
- Create, read, update, and delete tasks
- Due dates and reminder dates for tasks
- Status tracking (pending, completed)
- Task translation using Google Translate API

### Technical Features
- Responsive React-based frontend
- RESTful API with Flask
- MySQL database with proper data modeling
- Docker containerization
- Kubernetes orchestration
- Multi-cloud deployment (GCP and AWS)

## Project Structure

```
.
├── api_backend.py            # API backend with SQLite (original)
├── api_backend_mysql.py      # API backend with MySQL support
├── aws-deployment.md         # AWS EC2 deployment guide
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # Frontend container definition
├── Dockerfile.api            # API backend container definition
├── gcloud-scripts/           # GCP deployment scripts
│   └── setup_vm.sh           # VM setup script
├── k8s/                      # Kubernetes manifests
│   ├── api-deployment.yaml   # API backend deployment
│   ├── frontend-deployment.yaml # Frontend deployment
│   └── mysql-deployment.yaml # MySQL database deployment
├── multi-cloud-integration.md # Multi-cloud architecture documentation
├── requirements.txt          # Python dependencies
├── templates/                # Frontend templates
│   └── index.html            # Main application page
└── todolist.py              # Frontend server
```

## Quick Start

### Local Development

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start the application with Docker Compose:
   ```
   docker-compose up -d
   ```
4. Access the application at http://localhost

### Google Cloud Deployment

1. Set up a GKE cluster
2. Apply Kubernetes manifests:
   ```
   kubectl apply -f k8s/mysql-deployment.yaml
   kubectl apply -f k8s/api-deployment.yaml
   kubectl apply -f k8s/frontend-deployment.yaml
   ```
3. Access the application via the exposed ingress

### AWS Deployment

Follow the instructions in `aws-deployment.md` for detailed deployment steps on AWS EC2.

## Technology Stack

### Frontend
- HTML5, CSS3, JavaScript
- Bootstrap 5 for responsive design
- jQuery for DOM manipulation
- Flatpickr for date picking
- Moment.js for date formatting

### Backend
- Python 3.11
- Flask for API development
- JWT for authentication
- Google Cloud Translate API for task translation

### Database
- MySQL 8.0 for production
- SQLite for development/testing

### DevOps
- Docker and Docker Compose for containerization
- Kubernetes for orchestration
- Google Kubernetes Engine (GKE) for cloud deployment
- AWS EC2 for multi-cloud deployment

## API Documentation

### Authentication

#### Register a new user
```
POST /api/register
Body: { "name": "User Name", "email": "user@example.com", "password": "password" }
```

#### Login
```
POST /api/login
Body: { "email": "user@example.com", "password": "password" }
```

### Task Management

#### Get all tasks
```
GET /api/items
Headers: { "x-access-token": "your_jwt_token" }
```

#### Add a new task
```
POST /api/items
Headers: { "x-access-token": "your_jwt_token" }
Body: { "what_to_do": "Task description", "due_date": "2023-05-01 10:00:00", "reminder_date": "2023-04-30 10:00:00" }
```

#### Update a task
```
PUT /api/items/<item_id>
Headers: { "x-access-token": "your_jwt_token" }
Body: { "status": "done" } // Or any other field to update
```

#### Delete a task
```
DELETE /api/items/<item_id>
Headers: { "x-access-token": "your_jwt_token" }
```

### Translation

#### Translate text
```
POST /api/translate
Headers: { "x-access-token": "your_jwt_token" }
Body: { "text": "Task description", "target_language": "fr" }
```

## Security Considerations

- JWT tokens for secure authentication
- Password hashing using PBKDF2
- HTTPS for all production communications
- Database credentials stored in secrets
- Principle of least privilege for all service accounts

## Multi-Cloud Architecture

This application is designed to run across multiple cloud providers (GCP and AWS) for high availability and disaster recovery. See `multi-cloud-integration.md` for detailed architecture documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
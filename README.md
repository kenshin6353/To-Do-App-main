# To-Do-App

## How to Run This Project

### Prerequisites
- Docker and Docker Compose installed on your system
- Git (to clone the repository)

### Quick Start
1. **Clone the repository** (if you haven't already):
   ```sh
   git clone <repository-url>
   cd To-Do-App-main
   ```

2. **Build and start all services**:
   ```sh
   docker-compose up --build
   ```

3. **Access the application**:
   - Frontend: `http://localhost:5173`
   - Backend API: `http://localhost:8080`

### What's Running
The application consists of multiple microservices:
- **Frontend**: React application (port 5173)
- **User Service**: Handles authentication and user management
- **Task Service**: Manages todo tasks and projects
- **Notification Service**: Handles notifications and alerts
- **Redis**: Message broker for async task processing
- **PostgreSQL**: Database for data persistence
- **Nginx**: Reverse proxy and load balancer

### Stopping the Application
To stop all services:
```sh
docker-compose down
```

### Development Mode
For development with hot reloading:
```sh
docker-compose up --build --watch
```
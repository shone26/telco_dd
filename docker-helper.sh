#!/bin/bash

# Docker Helper Script for Telecom Application
# This script provides convenient commands for Docker operations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if docker-compose is available
check_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
}

# Function to setup environment
setup_env() {
    print_header "Setting up Environment"
    
    if [ ! -f .env ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please edit .env file with your configuration before starting services"
    else
        print_status ".env file already exists"
    fi
    
    # Create necessary directories
    mkdir -p nginx/ssl
    mkdir -p database
    mkdir -p logs
    
    print_status "Environment setup complete"
}

# Function to build services
build_services() {
    print_header "Building Services"
    check_docker
    check_compose
    
    print_status "Building all services..."
    docker-compose build --no-cache
    print_status "Build complete"
}

# Function to start services
start_services() {
    print_header "Starting Services"
    check_docker
    check_compose
    
    print_status "Starting all services..."
    docker-compose up -d
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    print_status "Checking service health..."
    docker-compose ps
    
    print_status "Services started successfully!"
    print_status "Frontend: http://localhost:3002"
    print_status "Backend API: http://localhost:5001/api"
    print_status "Nginx Proxy: http://localhost:80"
}

# Function to stop services
stop_services() {
    print_header "Stopping Services"
    check_docker
    check_compose
    
    print_status "Stopping all services..."
    docker-compose down
    print_status "Services stopped"
}

# Function to restart services
restart_services() {
    print_header "Restarting Services"
    stop_services
    start_services
}

# Function to view logs
view_logs() {
    print_header "Viewing Logs"
    check_docker
    check_compose
    
    if [ -z "$1" ]; then
        print_status "Showing logs for all services..."
        docker-compose logs -f
    else
        print_status "Showing logs for service: $1"
        docker-compose logs -f "$1"
    fi
}

# Function to run tests
run_tests() {
    print_header "Running Tests"
    check_docker
    check_compose
    
    print_status "Starting test runner..."
    docker-compose --profile testing up --build test_runner
    
    print_status "Tests completed"
}

# Function to clean up
cleanup() {
    print_header "Cleaning Up"
    check_docker
    check_compose
    
    print_warning "This will remove all containers, volumes, and images"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Stopping and removing containers..."
        docker-compose down -v --remove-orphans
        
        print_status "Removing images..."
        docker-compose down --rmi all
        
        print_status "Pruning Docker system..."
        docker system prune -f
        
        print_status "Cleanup complete"
    else
        print_status "Cleanup cancelled"
    fi
}

# Function to backup database
backup_db() {
    print_header "Database Backup"
    check_docker
    check_compose
    
    BACKUP_DIR="./backups"
    mkdir -p "$BACKUP_DIR"
    
    BACKUP_FILE="$BACKUP_DIR/telecom_db_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    print_status "Creating database backup..."
    docker-compose exec -T database pg_dump -U telecom_user telecom_db > "$BACKUP_FILE"
    
    print_status "Backup created: $BACKUP_FILE"
}

# Function to restore database
restore_db() {
    print_header "Database Restore"
    check_docker
    check_compose
    
    if [ -z "$1" ]; then
        print_error "Please provide backup file path"
        print_status "Usage: $0 restore-db <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Backup file not found: $1"
        exit 1
    fi
    
    print_warning "This will overwrite the current database"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Restoring database from: $1"
        docker-compose exec -T database psql -U telecom_user telecom_db < "$1"
        print_status "Database restored successfully"
    else
        print_status "Restore cancelled"
    fi
}

# Function to show service status
show_status() {
    print_header "Service Status"
    check_docker
    check_compose
    
    print_status "Container status:"
    docker-compose ps
    
    echo
    print_status "Resource usage:"
    docker stats --no-stream
    
    echo
    print_status "Health checks:"
    echo "Backend Health: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/health/ || echo "Failed")"
    echo "Frontend Health: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:3002/ || echo "Failed")"
    echo "Nginx Health: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:80/health || echo "Failed")"
}

# Function to access service shell
shell_access() {
    print_header "Shell Access"
    check_docker
    check_compose
    
    if [ -z "$1" ]; then
        print_error "Please specify service name"
        print_status "Available services: backend, frontend, database, redis"
        exit 1
    fi
    
    case "$1" in
        backend)
            print_status "Accessing backend shell..."
            docker-compose exec backend bash
            ;;
        frontend)
            print_status "Accessing frontend shell..."
            docker-compose exec frontend sh
            ;;
        database)
            print_status "Accessing database shell..."
            docker-compose exec database psql -U telecom_user telecom_db
            ;;
        redis)
            print_status "Accessing Redis shell..."
            docker-compose exec redis redis-cli
            ;;
        *)
            print_error "Unknown service: $1"
            print_status "Available services: backend, frontend, database, redis"
            exit 1
            ;;
    esac
}

# Function to show help
show_help() {
    echo "Docker Helper Script for Telecom Application"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  setup           Setup environment and create .env file"
    echo "  build           Build all Docker services"
    echo "  start           Start all services"
    echo "  stop            Stop all services"
    echo "  restart         Restart all services"
    echo "  logs [service]  View logs (all services or specific service)"
    echo "  test            Run test suite"
    echo "  status          Show service status and health"
    echo "  shell <service> Access service shell (backend|frontend|database|redis)"
    echo "  backup-db       Create database backup"
    echo "  restore-db <file> Restore database from backup"
    echo "  cleanup         Remove all containers, volumes, and images"
    echo "  help            Show this help message"
    echo
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 start"
    echo "  $0 logs backend"
    echo "  $0 shell database"
    echo "  $0 backup-db"
    echo "  $0 restore-db ./backups/backup.sql"
}

# Main script logic
case "$1" in
    setup)
        setup_env
        ;;
    build)
        build_services
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        view_logs "$2"
        ;;
    test)
        run_tests
        ;;
    status)
        show_status
        ;;
    shell)
        shell_access "$2"
        ;;
    backup-db)
        backup_db
        ;;
    restore-db)
        restore_db "$2"
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac

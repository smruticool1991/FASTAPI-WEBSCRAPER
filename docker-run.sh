#!/bin/bash

# Docker deployment script for Website Analysis API
set -e

echo "🚀 Website Analysis API Docker Deployment"
echo "=========================================="

# Function to show usage
show_usage() {
    echo "Usage: $0 [dev|prod|stop|logs|status]"
    echo ""
    echo "Commands:"
    echo "  dev     - Start development environment"
    echo "  prod    - Start production environment"
    echo "  stop    - Stop all containers"
    echo "  logs    - Show container logs"
    echo "  status  - Show container status"
    echo "  clean   - Remove all containers and volumes"
    echo ""
    exit 1
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    echo "📁 Creating necessary directories..."
    mkdir -p logs backups ssl
    echo "✅ Directories created"
}

# Development environment
start_dev() {
    echo "🔧 Starting development environment..."
    create_directories
    
    docker-compose -f docker-compose.yml up -d
    
    echo "✅ Development environment started!"
    echo ""
    echo "🌐 API available at: http://localhost:8000"
    echo "📚 API documentation: http://localhost:8000/docs"
    echo "❤️  Health check: http://localhost:8000/health"
    echo ""
    echo "📝 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
}

# Production environment
start_prod() {
    echo "🏭 Starting production environment..."
    create_directories
    
    # Check for required environment variables
    if [ -z "$DB_PASSWORD" ]; then
        echo "⚠️  Warning: DB_PASSWORD not set, using default"
    fi
    
    if [ -z "$GRAFANA_PASSWORD" ]; then
        echo "⚠️  Warning: GRAFANA_PASSWORD not set, using default"
    fi
    
    docker-compose -f docker-compose.prod.yml up -d
    
    echo "✅ Production environment started!"
    echo ""
    echo "🌐 API available at: http://localhost:8000"
    echo "🔍 Monitoring: http://localhost:9090 (Prometheus)"
    echo "📊 Dashboard: http://localhost:3000 (Grafana)"
    echo "🗄️  Database: localhost:5432"
    echo "💾 Cache: localhost:6379"
    echo ""
    echo "📝 To view logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo "🛑 To stop: docker-compose -f docker-compose.prod.yml down"
}

# Stop containers
stop_containers() {
    echo "🛑 Stopping containers..."
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose -f docker-compose.yml down
    fi
    
    if [ -f "docker-compose.prod.yml" ]; then
        docker-compose -f docker-compose.prod.yml down
    fi
    
    echo "✅ All containers stopped"
}

# Show logs
show_logs() {
    echo "📝 Showing container logs..."
    
    if docker-compose ps | grep -q "website-analyzer-api"; then
        docker-compose logs -f --tail=100
    elif docker-compose -f docker-compose.prod.yml ps | grep -q "website-analyzer-api-prod"; then
        docker-compose -f docker-compose.prod.yml logs -f --tail=100
    else
        echo "❌ No running containers found"
    fi
}

# Show status
show_status() {
    echo "📊 Container status:"
    echo ""
    
    if [ -f "docker-compose.yml" ]; then
        echo "Development environment:"
        docker-compose ps
        echo ""
    fi
    
    if [ -f "docker-compose.prod.yml" ]; then
        echo "Production environment:"
        docker-compose -f docker-compose.prod.yml ps
    fi
}

# Clean up everything
clean_all() {
    echo "🧹 Cleaning up all containers and volumes..."
    read -p "This will remove all data. Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f docker-compose.yml down -v --remove-orphans 2>/dev/null || true
        docker-compose -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
        
        # Remove built images
        docker image rm website_analyzer_api 2>/dev/null || true
        docker image rm test_website-analyzer-api 2>/dev/null || true
        
        echo "✅ Cleanup completed"
    else
        echo "❌ Cleanup cancelled"
    fi
}

# Main script logic
check_docker

case "${1:-}" in
    "dev")
        start_dev
        ;;
    "prod")
        start_prod
        ;;
    "stop")
        stop_containers
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "clean")
        clean_all
        ;;
    *)
        show_usage
        ;;
esac
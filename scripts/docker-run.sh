#!/bin/bash
# =============================================================================
# Verdant Docker Helper Script
# =============================================================================
#
# Usage:
#   ./scripts/docker-run.sh build      # Build all images
#   ./scripts/docker-run.sh up         # Start API + Dashboard
#   ./scripts/docker-run.sh test       # Run tests
#   ./scripts/docker-run.sh sandbox    # Run sandbox
#   ./scripts/docker-run.sh jupyter    # Start Jupyter
#   ./scripts/docker-run.sh dev        # Start development shell
#   ./scripts/docker-run.sh logs       # View logs
#   ./scripts/docker-run.sh down       # Stop all services
#   ./scripts/docker-run.sh clean      # Clean up containers and images
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project name
PROJECT="verdant"

# Print colored message
print_msg() {
    echo -e "${BLUE}[${PROJECT}]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[${PROJECT}]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[${PROJECT}]${NC} $1"
}

print_error() {
    echo -e "${RED}[${PROJECT}]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Build images
build() {
    print_msg "Building Docker images..."
    docker-compose build --parallel
    print_success "Build complete!"
}

# Start main services (API + Dashboard)
up() {
    print_msg "Starting API and Dashboard..."
    docker-compose up -d api dashboard
    print_success "Services started!"
    echo ""
    echo "  API:       http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    echo "  Dashboard: http://localhost:8501"
    echo ""
}

# Run tests
test() {
    print_msg "Running tests..."
    docker-compose run --rm tests
    print_success "Tests complete! Coverage report: ./htmlcov/index.html"
}

# Run sandbox
sandbox() {
    print_msg "Running sandbox..."
    docker-compose run --rm sandbox
    print_success "Sandbox complete! Report: ./sandbox_report.html"
}

# Start Jupyter
jupyter() {
    print_msg "Starting Jupyter Lab..."
    docker-compose --profile development up -d jupyter
    print_success "Jupyter started at http://localhost:8888"
}

# Development shell
dev() {
    print_msg "Starting development shell..."
    docker-compose --profile development run --rm dev
}

# View logs
logs() {
    docker-compose logs -f "${@:-api dashboard}"
}

# Stop all services
down() {
    print_msg "Stopping all services..."
    docker-compose --profile development --profile testing down
    print_success "All services stopped."
}

# Clean up
clean() {
    print_warning "Cleaning up containers, images, and volumes..."
    docker-compose --profile development --profile testing down -v --rmi local
    docker system prune -f
    print_success "Cleanup complete!"
}

# Status
status() {
    print_msg "Service status:"
    docker-compose ps
}

# Health check
health() {
    print_msg "Checking service health..."

    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API: Healthy"
    else
        print_error "API: Not responding"
    fi

    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        print_success "Dashboard: Healthy"
    else
        print_error "Dashboard: Not responding"
    fi
}

# Show help
help() {
    echo "Verdant Docker Helper"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  build     Build all Docker images"
    echo "  up        Start API and Dashboard services"
    echo "  test      Run test suite with coverage"
    echo "  sandbox   Run interactive sandbox tests"
    echo "  jupyter   Start Jupyter Lab server"
    echo "  dev       Start development shell"
    echo "  logs      View service logs (optional: service name)"
    echo "  status    Show service status"
    echo "  health    Check service health"
    echo "  down      Stop all services"
    echo "  clean     Remove containers, images, and volumes"
    echo "  help      Show this help message"
}

# Main
check_docker

case "${1:-help}" in
    build)   build ;;
    up)      up ;;
    test)    test ;;
    sandbox) sandbox ;;
    jupyter) jupyter ;;
    dev)     dev ;;
    logs)    shift; logs "$@" ;;
    status)  status ;;
    health)  health ;;
    down)    down ;;
    clean)   clean ;;
    help)    help ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac

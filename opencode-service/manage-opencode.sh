#!/bin/bash
# OpenCode Docker Management Script for Auto-Code
# Manages OpenCode AI containers for isolated development tasks

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load environment variables from .env if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Configuration
CONTAINER_NAME="autocode-opencode"
IMAGE_NAME="autocode-opencode-service"
DOCKERFILE="Dockerfile"
WORKSPACE_DIR="/home/ubuntu/workspace"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker Desktop."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker Desktop."
        exit 1
    fi
    
    # Check GH_TOKEN
    if [ -z "$GH_TOKEN" ]; then
        log_warning "GH_TOKEN is not set. GitHub authentication may fail."
        log_info "Export your GitHub token: export GH_TOKEN=your_token"
    fi
    
    # Check SSH key
    if [ ! -f "$HOME/.ssh/id_ed25519" ] && [ ! -f "$HOME/.ssh/id_rsa" ]; then
        log_warning "SSH key not found. Git operations may fail."
    fi
    
    # Check OpenCode auth
    if [ ! -f "$HOME/.local/share/opencode/auth.json" ]; then
        log_warning "OpenCode auth file not found."
        log_info "Run 'opencode auth login' to authenticate."
    fi
    
    log_success "Prerequisites check completed."
}

# Function to build the Docker image
build_image() {
    log_info "Building Docker image: $IMAGE_NAME..."
    
    cd "$(dirname "$0")"
    
    docker build -t $IMAGE_NAME -f $DOCKERFILE .
    
    if [ $? -ne 0 ]; then
        log_error "Docker build failed. Exiting."
        exit 1
    fi
    
    log_success "Build successful: $IMAGE_NAME"
}

# Function to start the container
start_container() {
    log_info "Starting OpenCode container: $CONTAINER_NAME..."
    
    # Prepare volume mounts
    VOLUMES=""
    
    # Mount SSH key (try ed25519 first, then rsa)
    if [ -f "$HOME/.ssh/id_ed25519" ]; then
        VOLUMES="$VOLUMES -v $HOME/.ssh/id_ed25519:/home/ubuntu/.ssh/id_ed25519:ro"
    elif [ -f "$HOME/.ssh/id_rsa" ]; then
        VOLUMES="$VOLUMES -v $HOME/.ssh/id_rsa:/home/ubuntu/.ssh/id_rsa:ro"
    fi
    
    # Mount OpenCode config
    if [ -d "$HOME/.config/opencode" ]; then
        VOLUMES="$VOLUMES -v $HOME/.config/opencode:/home/ubuntu/.config/opencode"
    fi
    
    # Mount OpenCode auth
    if [ -f "$HOME/.local/share/opencode/auth.json" ]; then
        VOLUMES="$VOLUMES -v $HOME/.local/share/opencode/auth.json:/home/ubuntu/.local/share/opencode/auth.json"
    fi
    
    # Run container
    docker run -dit --name $CONTAINER_NAME \
        -h $CONTAINER_NAME \
        -e GH_TOKEN \
        -w $WORKSPACE_DIR \
        $VOLUMES \
        $IMAGE_NAME /bin/bash
    
    log_success "Container started: $CONTAINER_NAME"
}

# Function to stop the container
stop_container() {
    log_info "Stopping container: $CONTAINER_NAME..."
    docker stop $CONTAINER_NAME
    log_success "Container stopped."
}

# Function to remove the container
remove_container() {
    log_info "Removing container: $CONTAINER_NAME..."
    docker rm $CONTAINER_NAME
    log_success "Container removed."
}

# Function to execute OpenCode in the container
execute_opencode() {
    local repo_path="$1"
    local ticket_prompt="$2"
    
    log_info "Executing OpenCode on: $repo_path"
    
    # Clone or pull repository
    docker exec -it $CONTAINER_NAME /bin/bash -c "
        cd $WORKSPACE_DIR
        if [ -d $repo_path ]; then
            cd $repo_path && git pull
        else
            git clone $repo_path
        fi
    "
    
    # Run OpenCode with the ticket prompt
    docker exec -it $CONTAINER_NAME /bin/bash -c "
        cd $WORKSPACE_DIR/$(basename $repo_path)
        echo '$ticket_prompt' | /home/ubuntu/.opencode/bin/opencode .
    "
}

# Function to show container status
status() {
    log_info "Container status:"
    
    if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
        log_success "Container is RUNNING"
        docker ps -f name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    elif [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
        log_warning "Container exists but is STOPPED"
    else
        log_warning "Container does NOT exist"
    fi
    
    # Show image info
    if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" != "" ]]; then
        log_info "Image: $IMAGE_NAME exists"
    else
        log_warning "Image: $IMAGE_NAME NOT found"
    fi
}

# Main command dispatcher
case "$1" in
    build)
        check_prerequisites
        build_image
        ;;
    
    start)
        check_prerequisites
        
        # Check if container exists and is running
        if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
            log_info "Container already running."
            exit 0
        elif [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
            log_warning "Container exists but is stopped. Removing..."
            remove_container
        fi
        
        # Build image if missing
        if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
            log_warning "Image not found. Building..."
            build_image
        fi
        
        start_container
        ;;
    
    stop)
        if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
            stop_container
        else
            log_warning "Container is not running."
        fi
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    remove)
        if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
            stop_container
        fi
        
        if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
            remove_container
        else
            log_warning "Container does not exist."
        fi
        ;;
    
    rebuild)
        $0 remove
        build_image
        $0 start
        ;;
    
    exec)
        if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
            docker exec -it $CONTAINER_NAME /bin/bash
        else
            log_error "Container is not running. Start it first with: $0 start"
            exit 1
        fi
        ;;
    
    status)
        status
        ;;
    
    logs)
        docker logs -f $CONTAINER_NAME
        ;;
    
    *)
        echo "Usage: $0 {build|start|stop|restart|remove|rebuild|exec|status|logs}"
        echo ""
        echo "Commands:"
        echo "  build     - Build the Docker image"
        echo "  start     - Start the OpenCode container"
        echo "  stop      - Stop the container"
        echo "  restart   - Restart the container"
        echo "  remove    - Remove the container"
        echo "  rebuild   - Rebuild image and restart container"
        echo "  exec      - Execute bash in the running container"
        echo "  status    - Show container and image status"
        echo "  logs      - Show container logs"
        echo ""
        echo "Environment variables:"
        echo "  GH_TOKEN  - GitHub personal access token"
        exit 1
        ;;
esac

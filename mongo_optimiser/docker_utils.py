"""
Docker utilities for managing local MongoDB containers.
"""
import time
import sys
from typing import Optional

try:
    import docker
    from docker.errors import DockerException, NotFound, APIError
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

from .config import MONGO_CONTAINER_NAME, MONGO_DOCKER_IMAGE


def is_docker_available() -> bool:
    """Check if Docker is available and accessible."""
    if not DOCKER_AVAILABLE:
        return False
    
    try:
        client = docker.from_env()
        client.ping()
        return True
    except (DockerException, Exception):
        return False


def is_container_running(container_name: str) -> bool:
    """Check if a Docker container is running."""
    if not DOCKER_AVAILABLE:
        return False
    
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        return container.status == 'running'
    except (NotFound, DockerException):
        return False


def start_mongodb_container() -> bool:
    """
    Start MongoDB container with profiling enabled.
    
    Returns:
        True if container started successfully, False otherwise
    """
    if not DOCKER_AVAILABLE:
        print("❌ Docker is not available. Please install docker package: pip install docker")
        return False
    
    if not is_docker_available():
        print("❌ Docker daemon is not running or not accessible")
        return False
    
    try:
        client = docker.from_env()
        
        # Check if container already exists
        try:
            container = client.containers.get(MONGO_CONTAINER_NAME)
            if container.status == 'running':
                print(f"✅ MongoDB container '{MONGO_CONTAINER_NAME}' is already running")
                return True
            elif container.status == 'exited':
                print(f"🔄 Starting existing MongoDB container '{MONGO_CONTAINER_NAME}'...")
                container.start()
                time.sleep(3)  # Give it time to start
                return True
        except NotFound:
            pass  # Container doesn't exist, we'll create it
        
        # Create and start new container
        print(f"🚀 Creating MongoDB container '{MONGO_CONTAINER_NAME}' with {MONGO_DOCKER_IMAGE}...")
        
        container = client.containers.run(
            MONGO_DOCKER_IMAGE,
            name=MONGO_CONTAINER_NAME,
            ports={'27017/tcp': 27017},
            detach=True,
            command=['mongod', '--profile', '2', '--slowms', '0'],  # Enable profiling for all operations
            remove=False  # Don't auto-remove so we can reuse
        )
        
        print(f"⏳ Waiting for MongoDB to be ready...")
        time.sleep(5)  # Give MongoDB time to start
        
        # Verify container is running
        container.reload()
        if container.status == 'running':
            print(f"✅ MongoDB container started successfully")
            print(f"📊 Profiling enabled: level 2, slowms 0")
            return True
        else:
            print(f"❌ Container failed to start. Status: {container.status}")
            return False
            
    except APIError as e:
        print(f"❌ Docker API error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error starting MongoDB container: {e}")
        return False


def stop_mongodb_container() -> bool:
    """
    Stop MongoDB container.
    
    Returns:
        True if container stopped successfully, False otherwise
    """
    if not DOCKER_AVAILABLE:
        return False
    
    try:
        client = docker.from_env()
        container = client.containers.get(MONGO_CONTAINER_NAME)
        
        if container.status == 'running':
            print(f"🛑 Stopping MongoDB container '{MONGO_CONTAINER_NAME}'...")
            container.stop()
            print(f"✅ Container stopped")
            return True
        else:
            print(f"ℹ️  Container '{MONGO_CONTAINER_NAME}' is not running")
            return True
            
    except NotFound:
        print(f"ℹ️  Container '{MONGO_CONTAINER_NAME}' not found")
        return True
    except Exception as e:
        print(f"❌ Error stopping container: {e}")
        return False


def cleanup_mongodb_container() -> bool:
    """
    Remove MongoDB container completely.
    
    Returns:
        True if container removed successfully, False otherwise
    """
    if not DOCKER_AVAILABLE:
        return False
    
    try:
        client = docker.from_env()
        container = client.containers.get(MONGO_CONTAINER_NAME)
        
        # Stop if running
        if container.status == 'running':
            container.stop()
        
        # Remove container
        container.remove()
        print(f"🗑️  MongoDB container '{MONGO_CONTAINER_NAME}' removed")
        return True
        
    except NotFound:
        print(f"ℹ️  Container '{MONGO_CONTAINER_NAME}' not found")
        return True
    except Exception as e:
        print(f"❌ Error removing container: {e}")
        return False


def get_container_logs() -> Optional[str]:
    """Get logs from MongoDB container."""
    if not DOCKER_AVAILABLE:
        return None
    
    try:
        client = docker.from_env()
        container = client.containers.get(MONGO_CONTAINER_NAME)
        return container.logs(tail=50).decode('utf-8')
    except Exception:
        return None

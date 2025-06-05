import os
import logging
from pathlib import Path
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnvironmentConfig:
    """
    Environment detection and configuration management for ComfyUI-Gradio integration.
    Automatically detects RunPod vs local development environment and provides 
    appropriate configuration for each.
    """
    
    def __init__(self):
        self.is_runpod = self._detect_runpod_environment()
        self.base_dir = self._get_base_directory()
        self.config = self._build_config()
        
        logger.info(f"Environment detected: {'RunPod' if self.is_runpod else 'Local'}")
        logger.info(f"Base directory: {self.base_dir}")
    
    def _detect_runpod_environment(self) -> bool:
        """
        Detect if we're running in a RunPod environment.
        RunPod environments typically have a /workspace directory.
        """
        runpod_indicators = [
            os.path.exists("/workspace"),
            os.environ.get("RUNPOD_POD_ID") is not None,
            os.path.exists("/workspace/learn_comfyui_apps")
        ]
        return any(runpod_indicators)
    
    def _get_base_directory(self) -> Path:
        """
        Get the appropriate base directory based on environment.
        """
        if self.is_runpod:
            return Path("/workspace/learn_comfyui_apps")
        else:
            # For local development, use the current working directory or detect from script location
            current_dir = Path.cwd()
            if "learn_comfyui_apps" in str(current_dir):
                # Find the root of the project
                parts = current_dir.parts
                try:
                    learn_index = parts.index("learn_comfyui_apps")
                    return Path(*parts[:learn_index + 1])
                except ValueError:
                    pass
            return current_dir
    
    def _build_config(self) -> Dict[str, Any]:
        """
        Build configuration dictionary based on detected environment.
        """
        # Server configuration
        if self.is_runpod:
            server_host = "0.0.0.0"
            comfyui_host = "0.0.0.0"
        else:
            server_host = "127.0.0.1"
            comfyui_host = "127.0.0.1"
        
        comfyui_port = 9000
        gradio_port = 9002
        
        config = {
            # Environment info
            "is_runpod": self.is_runpod,
            "base_dir": self.base_dir,
            
            # Server configuration
            "server": {
                "host": server_host,
                "port": gradio_port,
                "debug": True
            },
            
            # ComfyUI configuration
            "comfyui": {
                "host": comfyui_host,
                "port": comfyui_port,
                "ws_url": f"ws://{comfyui_host}:{comfyui_port}/ws",
                "http_url": f"http://{comfyui_host}:{comfyui_port}",
                "api_url": f"http://{comfyui_host}:{comfyui_port}/prompt",
                "history_url": f"http://{comfyui_host}:{comfyui_port}/history"
            },
            
            # File paths
            "paths": {
                "app_dir": self.base_dir / "app",
                "workflows_dir": self.base_dir / "app" / "workflows",
                "output_dir": self.base_dir / "app" / "outputs",
                "save_dir": self.base_dir / "app" / "outputs" / "save_linkedin",
                "comfyui_dir": self.base_dir / "ComfyUI",
                "workflow_file": self.base_dir / "app" / "workflows" / "linkedin_photomaker_solution.json"
            },
            
            # Application settings
            "app": {
                "client_id": "06a96135-59b2-4a29-b7c8-a83fc011ea63",
                "max_queue_size": 100,
                "message_timeout": 30,
                "reconnect_attempts": 5,
                "reconnect_delay": 2
            }
        }
        
        # Ensure output directories exist
        self._ensure_directories_exist(config["paths"])
        
        return config
    
    def _ensure_directories_exist(self, paths: Dict[str, Path]):
        """
        Create necessary directories if they don't exist.
        """
        directories_to_create = ["output_dir", "save_dir"]
        
        for dir_key in directories_to_create:
            if dir_key in paths:
                dir_path = paths[dir_key]
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Ensured directory exists: {dir_path}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        Example: config.get("comfyui.host") returns the ComfyUI host
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def validate_environment(self) -> bool:
        """
        Validate that the current environment is properly configured.
        Returns True if environment is valid, False otherwise.
        """
        validation_checks = []
        
        # Check if base directory exists
        validation_checks.append(
            self.base_dir.exists()
        )
        
        # Check if workflow file exists
        workflow_file = Path(self.get("paths.workflow_file"))
        validation_checks.append(
            workflow_file.exists()
        )
        
        # Check if app directory exists
        app_dir = Path(self.get("paths.app_dir"))
        validation_checks.append(
            app_dir.exists()
        )
        
        is_valid = all(validation_checks)
        
        if not is_valid:
            logger.error("Environment validation failed:")
            logger.error(f"  Base directory exists: {self.base_dir.exists()}")
            logger.error(f"  Workflow file exists: {workflow_file.exists()}")
            logger.error(f"  App directory exists: {app_dir.exists()}")
        else:
            logger.info("Environment validation passed")
        
        return is_valid

# Global configuration instance
config = EnvironmentConfig()

# Convenience functions for common access patterns
def get_comfyui_ws_url() -> str:
    """Get ComfyUI WebSocket URL for current environment."""
    return config.get("comfyui.ws_url")

def get_comfyui_api_url() -> str:
    """Get ComfyUI API URL for current environment."""
    return config.get("comfyui.api_url")

def get_save_directory() -> Path:
    """Get the save directory for generated images."""
    return Path(config.get("paths.save_dir"))

def get_workflow_file() -> Path:
    """Get the path to the workflow JSON file."""
    return Path(config.get("paths.workflow_file"))

def is_runpod() -> bool:
    """Check if running in RunPod environment."""
    return config.get("is_runpod", False)

def get_client_id() -> str:
    """Get the default client ID for ComfyUI connections."""
    return config.get("app.client_id")

# Validation on import
if not config.validate_environment():
    logger.warning("Environment validation failed. Some features may not work correctly.") 
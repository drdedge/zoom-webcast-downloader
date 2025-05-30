# utils/config_manager.py
"""
Configuration Manager
Handles application configuration from multiple sources:
1. Default values
2. Configuration file
3. Environment variables (.env file and system)
4. Command-line arguments (override)
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

from .logger_setup import setup_logger

logger = setup_logger(name="config_manager", level=logging.DEBUG)


@dataclass
class AzureConfig:
    """Azure service configuration"""
    speech_key: str = ""
    speech_endpoint: str = ""
    openai_endpoint: str = ""
    openai_key: str = ""
    model_name: str = "azure/gpt-4"
    api_version: str = "2024-02-15-preview"
    
    def validate(self) -> bool:
        """Check if all required fields are set"""
        required = ['speech_key', 'speech_endpoint', 'openai_endpoint', 'openai_key']
        return all(getattr(self, field) for field in required)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for compatibility"""
        return {
            'speech_key': self.speech_key,
            'speech_endpoint': self.speech_endpoint,
            'azure_endpoint': self.openai_endpoint,
            'api_key': self.openai_key,
            'model_name': self.model_name,
            'api_version': self.api_version
        }


@dataclass
class ProcessingConfig:
    """Processing options configuration"""
    extract_frames: bool = False
    create_ppt: bool = False
    transcribe: bool = True
    generate_summary: bool = True
    frame_threshold: int = 30
    max_speakers: int = 10
    timeout: int = 30
    headless: bool = True


@dataclass
class AppConfig:
    """Complete application configuration"""
    azure: AzureConfig = field(default_factory=AzureConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    output_dir: str = "output"
    log_to_file: bool = True
    log_dir: str = "logs"


class ConfigManager:
    """Manages application configuration from multiple sources"""
    
    DEFAULT_CONFIG_PATHS = [
        "config.json",
        ".config.json",
        "~/.zoom_processor/config.json",
        "/etc/zoom_processor/config.json"
    ]
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config = AppConfig()
        self.config_file = config_file
        self.logger = logger
        
        # Load .env file if available
        if HAS_DOTENV:
            # Try to load from multiple locations
            env_files = ['.env', '.env.local', Path.home() / '.zoom_processor' / '.env']
            for env_file in env_files:
                if Path(env_file).exists():
                    load_dotenv(env_file)
                    self.logger.debug(f"Loaded environment from: {env_file}")
                    break
        
        # Load configuration in order of precedence
        self._load_defaults()
        self._load_from_file()
        self._load_from_env()
    
    def _load_defaults(self):
        """Load default configuration"""
        # Defaults are already set in dataclass definitions
        pass
    
    def _load_from_file(self):
        """Load configuration from file"""
        config_paths = []
        
        # Add provided config file first
        if self.config_file:
            config_paths.append(self.config_file)
        
        # Add default paths
        config_paths.extend([Path(p).expanduser() for p in self.DEFAULT_CONFIG_PATHS])
        
        # Try each path
        for path in config_paths:
            try:
                if Path(path).exists():
                    with open(path, 'r') as f:
                        data = json.load(f)
                        self._update_config(data)
                        self.logger.info(f"Loaded configuration from: {path}")
                        return
            except Exception as e:
                self.logger.debug(f"Could not load config from {path}: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        env_mappings = {
            # Azure settings
            'AZURE_SPEECH_KEY': ('azure', 'speech_key'),
            'AZURE_SPEECH_ENDPOINT': ('azure', 'speech_endpoint'),
            'AZURE_OPENAI_ENDPOINT': ('azure', 'openai_endpoint'),
            'AZURE_OPENAI_KEY': ('azure', 'openai_key'),
            'AZURE_MODEL_NAME': ('azure', 'model_name'),
            'AZURE_API_VERSION': ('azure', 'api_version'),
            
            # Processing settings
            'ZOOM_EXTRACT_FRAMES': ('processing', 'extract_frames', bool),
            'ZOOM_CREATE_PPT': ('processing', 'create_ppt', bool),
            'ZOOM_TRANSCRIBE': ('processing', 'transcribe', bool),
            'ZOOM_GENERATE_SUMMARY': ('processing', 'generate_summary', bool),
            'ZOOM_TIMEOUT': ('processing', 'timeout', int),
            'ZOOM_HEADLESS': ('processing', 'headless', bool),
            
            # General settings
            'ZOOM_OUTPUT_DIR': ('output_dir',),
            'ZOOM_LOG_TO_FILE': ('log_to_file', bool),
            'ZOOM_LOG_DIR': ('log_dir',),
        }
        
        for env_var, mapping in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(mapping, value)
    
    def _update_config(self, data: dict):
        """Update configuration from dictionary"""
        if 'azure' in data:
            for key, value in data['azure'].items():
                if hasattr(self.config.azure, key):
                    setattr(self.config.azure, key, value)
        
        if 'processing' in data:
            for key, value in data['processing'].items():
                if hasattr(self.config.processing, key):
                    setattr(self.config.processing, key, value)
        
        # Top-level settings
        for key in ['output_dir', 'log_to_file', 'log_dir']:
            if key in data:
                setattr(self.config, key, data[key])
    
    def _set_nested_value(self, mapping: tuple, value: Any):
        """Set a nested configuration value"""
        if len(mapping) == 1:
            # Top-level setting
            setattr(self.config, mapping[0], value)
        elif len(mapping) >= 2:
            # Nested setting
            section = getattr(self.config, mapping[0])
            attr_name = mapping[1]
            
            # Type conversion if specified
            if len(mapping) > 2 and mapping[2] == bool:
                value = value.lower() in ('true', '1', 'yes', 'on')
            elif len(mapping) > 2 and mapping[2] == int:
                value = int(value)
            
            setattr(section, attr_name, value)
    
    def override_with_args(self, **kwargs):
        """Override configuration with command-line arguments"""
        # Map CLI arguments to config structure
        mappings = {
            'speech_key': ('azure', 'speech_key'),
            'speech_endpoint': ('azure', 'speech_endpoint'),
            'azure_endpoint': ('azure', 'openai_endpoint'),
            'api_key': ('azure', 'openai_key'),
            'model_name': ('azure', 'model_name'),
            'extract_frames': ('processing', 'extract_frames'),
            'create_ppt': ('processing', 'create_ppt'),
            'transcribe': ('processing', 'transcribe'),
            'generate_summary': ('processing', 'generate_summary'),
            'timeout': ('processing', 'timeout'),
            'headless': ('processing', 'headless'),
            'output_dir': ('output_dir',),
            'log_to_file': ('log_to_file',),
        }
        
        for arg_name, value in kwargs.items():
            if value is not None and arg_name in mappings:
                self._set_nested_value(mappings[arg_name], value)
    
    def save_to_file(self, filepath: Optional[str] = None):
        """Save current configuration to file"""
        if not filepath:
            filepath = self.config_file or "config.json"
        
        config_dict = {
            'azure': asdict(self.config.azure),
            'processing': asdict(self.config.processing),
            'output_dir': self.config.output_dir,
            'log_to_file': self.config.log_to_file,
            'log_dir': self.config.log_dir
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        self.logger.info(f"Configuration saved to: {filepath}")
    
    def create_template(self, filepath: str = "config.template.json"):
        """Create a configuration template file"""
        template = {
            "azure": {
                "speech_key": "your-speech-key-here",
                "speech_endpoint": "https://your-resource.cognitiveservices.azure.com",
                "openai_endpoint": "https://your-resource.openai.azure.com/",
                "openai_key": "your-openai-key-here",
                "model_name": "azure/gpt-4",
                "api_version": "2024-02-15-preview"
            },
            "processing": {
                "extract_frames": False,
                "create_ppt": False,
                "transcribe": True,
                "generate_summary": True,
                "frame_threshold": 30,
                "max_speakers": 10,
                "timeout": 30,
                "headless": True
            },
            "output_dir": "output",
            "log_to_file": True,
            "log_dir": "logs"
        }
        
        with open(filepath, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"Configuration template created: {filepath}")
        print("\nYou can also use environment variables (.env file or system):")
        print("  - Copy .env.template to .env and update with your values")
        print("  - Or set system environment variables (AZURE_SPEECH_KEY, etc.)")
    
    def validate(self) -> bool:
        """Validate configuration"""
        return self.config.azure.validate()
    
    def get_azure_config(self) -> dict:
        """Get Azure configuration as dictionary"""
        return self.config.azure.to_dict()
    
    def __repr__(self):
        """String representation"""
        return f"ConfigManager(azure_configured={self.config.azure.validate()})"
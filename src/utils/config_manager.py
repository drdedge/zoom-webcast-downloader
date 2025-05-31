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
class BrowserConfig:
    """Browser configuration for zoom downloads"""
    impersonate_profile: str = "chrome116"
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 2
    network_timeout: int = 300
    chunk_size: int = 8192


@dataclass
class ZoomOutputConfig:
    """Zoom output configuration"""
    save_variables: bool = True
    auto_filename_from_topic: bool = True


@dataclass
class ZoomDownloadConfig:
    """Zoom download configuration"""
    headless: bool = True
    timeout: int = 30
    max_wait_password: int = 15
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    output: ZoomOutputConfig = field(default_factory=ZoomOutputConfig)


@dataclass
class ProcessingConfig:
    """Processing options configuration"""
    extract_frames: bool = False
    create_ppt: bool = False
    transcribe: bool = True
    generate_summary: bool = True
    frame_threshold: int = 30
    max_speakers: int = 10
    timeout: int = 60


@dataclass
class AppConfig:
    """Complete application configuration"""
    azure: AzureConfig = field(default_factory=AzureConfig)
    zoom_download: ZoomDownloadConfig = field(default_factory=ZoomDownloadConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    output_dir: str = "output"
    log_to_file: bool = True
    log_dir: str = "logs"
    debug: bool = False


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
            
            # Zoom download settings
            'ZOOM_DOWNLOAD_HEADLESS': ('zoom_download', 'headless', bool),
            'ZOOM_DOWNLOAD_TIMEOUT': ('zoom_download', 'timeout', int),
            'ZOOM_DOWNLOAD_MAX_WAIT': ('zoom_download', 'max_wait_password', int),
            'ZOOM_BROWSER_PROFILE': ('zoom_download', 'browser', 'impersonate_profile'),
            'ZOOM_USER_AGENT': ('zoom_download', 'browser', 'user_agent'),
            'ZOOM_MAX_ATTEMPTS': ('zoom_download', 'retry', 'max_attempts', int),
            'ZOOM_NETWORK_TIMEOUT': ('zoom_download', 'retry', 'network_timeout', int),
            'ZOOM_CHUNK_SIZE': ('zoom_download', 'retry', 'chunk_size', int),
            'ZOOM_SAVE_VARIABLES': ('zoom_download', 'output', 'save_variables', bool),
            'ZOOM_AUTO_FILENAME': ('zoom_download', 'output', 'auto_filename_from_topic', bool),
            
            # Processing settings
            'ZOOM_EXTRACT_FRAMES': ('processing', 'extract_frames', bool),
            'ZOOM_CREATE_PPT': ('processing', 'create_ppt', bool),
            'ZOOM_TRANSCRIBE': ('processing', 'transcribe', bool),
            'ZOOM_GENERATE_SUMMARY': ('processing', 'generate_summary', bool),
            'ZOOM_FRAME_THRESHOLD': ('processing', 'frame_threshold', int),
            'ZOOM_MAX_SPEAKERS': ('processing', 'max_speakers', int),
            'ZOOM_PROCESSING_TIMEOUT': ('processing', 'timeout', int),
            
            # General settings
            'ZOOM_OUTPUT_DIR': ('output_dir',),
            'ZOOM_LOG_TO_FILE': ('log_to_file', bool),
            'ZOOM_LOG_DIR': ('log_dir',),
            'DEBUG': ('debug', bool),
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
        
        if 'zoom_download' in data:
            zoom_data = data['zoom_download']
            
            # Handle nested browser config
            if 'browser' in zoom_data:
                for key, value in zoom_data['browser'].items():
                    if hasattr(self.config.zoom_download.browser, key):
                        setattr(self.config.zoom_download.browser, key, value)
            
            # Handle nested retry config
            if 'retry' in zoom_data:
                for key, value in zoom_data['retry'].items():
                    if hasattr(self.config.zoom_download.retry, key):
                        setattr(self.config.zoom_download.retry, key, value)
            
            # Handle nested output config
            if 'output' in zoom_data:
                for key, value in zoom_data['output'].items():
                    if hasattr(self.config.zoom_download.output, key):
                        setattr(self.config.zoom_download.output, key, value)
            
            # Handle top-level zoom_download settings
            for key, value in zoom_data.items():
                if key not in ['browser', 'retry', 'output'] and hasattr(self.config.zoom_download, key):
                    setattr(self.config.zoom_download, key, value)
        
        if 'processing' in data:
            for key, value in data['processing'].items():
                if hasattr(self.config.processing, key):
                    setattr(self.config.processing, key, value)
        
        # Top-level settings
        for key in ['output_dir', 'log_to_file', 'log_dir', 'debug']:
            if key in data:
                setattr(self.config, key, data[key])
    
    def _set_nested_value(self, mapping: tuple, value: Any):
        """Set a nested configuration value"""
        if len(mapping) == 1:
            # Top-level setting
            setattr(self.config, mapping[0], value)
        elif len(mapping) == 2:
            # Nested setting (e.g., azure.speech_key)
            section = getattr(self.config, mapping[0])
            attr_name = mapping[1]
            
            # Type conversion if specified
            if len(mapping) > 2 and mapping[2] == bool:
                value = value.lower() in ('true', '1', 'yes', 'on')
            elif len(mapping) > 2 and mapping[2] == int:
                value = int(value)
            
            setattr(section, attr_name, value)
        elif len(mapping) >= 3:
            # Double-nested setting (e.g., zoom_download.browser.user_agent)
            section = getattr(self.config, mapping[0])
            subsection = getattr(section, mapping[1])
            attr_name = mapping[2]
            
            # Type conversion if specified
            if len(mapping) > 3 and mapping[3] == bool:
                value = value.lower() in ('true', '1', 'yes', 'on')
            elif len(mapping) > 3 and mapping[3] == int:
                value = int(value)
            
            setattr(subsection, attr_name, value)
    
    def override_with_args(self, **kwargs):
        """Override configuration with command-line arguments"""
        # Map CLI arguments to config structure
        mappings = {
            # Azure settings
            'speech_key': ('azure', 'speech_key'),
            'speech_endpoint': ('azure', 'speech_endpoint'),
            'azure_endpoint': ('azure', 'openai_endpoint'),
            'api_key': ('azure', 'openai_key'),
            'model_name': ('azure', 'model_name'),
            
            # Zoom download settings
            'headless': ('zoom_download', 'headless'),
            'zoom_timeout': ('zoom_download', 'timeout'),
            'max_attempts': ('zoom_download', 'retry', 'max_attempts'),
            
            # Processing settings
            'extract_frames': ('processing', 'extract_frames'),
            'create_ppt': ('processing', 'create_ppt'),
            'transcribe': ('processing', 'transcribe'),
            'generate_summary': ('processing', 'generate_summary'),
            'timeout': ('processing', 'timeout'),
            
            # General settings
            'output_dir': ('output_dir',),
            'log_to_file': ('log_to_file',),
            'debug': ('debug',),
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
            'zoom_download': {
                'headless': self.config.zoom_download.headless,
                'timeout': self.config.zoom_download.timeout,
                'max_wait_password': self.config.zoom_download.max_wait_password,
                'browser': asdict(self.config.zoom_download.browser),
                'retry': asdict(self.config.zoom_download.retry),
                'output': asdict(self.config.zoom_download.output)
            },
            'processing': asdict(self.config.processing),
            'output_dir': self.config.output_dir,
            'log_to_file': self.config.log_to_file,
            'log_dir': self.config.log_dir,
            'debug': self.config.debug
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=4)
        
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
            "zoom_download": {
                "headless": True,
                "timeout": 30,
                "max_wait_password": 15,
                "browser": {
                    "impersonate_profile": "chrome116",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
                },
                "retry": {
                    "max_attempts": 2,
                    "network_timeout": 300,
                    "chunk_size": 8192
                },
                "output": {
                    "save_variables": True,
                    "auto_filename_from_topic": True
                }
            },
            "processing": {
                "extract_frames": False,
                "create_ppt": False,
                "transcribe": True,
                "generate_summary": True,
                "frame_threshold": 30,
                "max_speakers": 10,
                "timeout": 60
            },
            "output_dir": "output",
            "log_to_file": True,
            "log_dir": "logs",
            "debug": False
        }
        
        with open(filepath, 'w') as f:
            json.dump(template, f, indent=4)
        
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
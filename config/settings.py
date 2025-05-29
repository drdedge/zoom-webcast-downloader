"""
Central configuration for Zoom Recording Processor
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DEFAULT_OUTPUT_DIR = os.getenv('DEFAULT_OUTPUT_DIR', 'output')

# Browser settings
BROWSER_CONFIG = {
    'headless': os.getenv('BROWSER_HEADLESS', 'false').lower() == 'true',
    'user_agent': os.getenv('BROWSER_USER_AGENT', 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    ),
    'impersonate_profile': 'chrome116'
}

# Network capture settings
CAPTURE_CONFIG = {
    'timeout': int(os.getenv('CAPTURE_TIMEOUT', 30)),
    'max_retries': int(os.getenv('CAPTURE_MAX_RETRIES', 2)),
    'cookie_accept_timeout': int(os.getenv('COOKIE_ACCEPT_TIMEOUT', 5))
}

# Download settings
DOWNLOAD_CONFIG = {
    'chunk_size': int(os.getenv('DOWNLOAD_CHUNK_SIZE', 8192)),
    'timeout': int(os.getenv('DOWNLOAD_TIMEOUT', 30)),
    'max_concurrent': int(os.getenv('MAX_CONCURRENT_DOWNLOADS', 3))
}

# Azure Cognitive Services
AZURE_CONFIG = {
    'speech_key': os.getenv('AZURE_SPEECH_KEY'),
    'speech_region': os.getenv('AZURE_SPEECH_REGION'),
    'text_analytics_key': os.getenv('AZURE_TEXT_ANALYTICS_KEY'),
    'text_analytics_endpoint': os.getenv('AZURE_TEXT_ANALYTICS_ENDPOINT'),
}

# Processing settings
PROCESSING_CONFIG = {
    'transcript_language': os.getenv('DEFAULT_TRANSCRIPT_LANGUAGE', 'en-US'),
    'frame_interval': int(os.getenv('DEFAULT_FRAME_INTERVAL', 5)),
    'enable_gpu': os.getenv('ENABLE_GPU_ACCELERATION', 'false').lower() == 'true',
    'max_workers': int(os.getenv('PROCESSING_MAX_WORKERS', 4))
}

# File naming patterns
FILE_PATTERNS = {
    'recording': '{meeting_topic}_{timestamp}.mp4',
    'transcript': '{recording_name}_transcript.txt',
    'summary': '{recording_name}_summary.docx',
    'presentation': '{recording_name}_slides.pptx',
    'frame': 'frame_{timestamp}.png'
}

# Logging configuration
LOGGING_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'debug_mode': os.getenv('DEBUG_MODE', 'false').lower() == 'true'
}

# Validation functions
def validate_azure_config():
    """Validate Azure configuration is complete"""
    required = ['speech_key', 'speech_region']
    missing = [k for k in required if not AZURE_CONFIG.get(k)]
    
    if missing:
        raise ValueError(f"Missing Azure configuration: {', '.join(missing)}")
    
    return True

def get_output_path(filename, output_dir=None):
    """Get full output path ensuring directory exists"""
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path / filename
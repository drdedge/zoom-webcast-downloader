# src/utils/common.py
"""Common utilities and constants"""

import os
import json
from datetime import datetime
from urllib.parse import urlparse
import click

# Browser fingerprint settings
IMPERSONATE_PROFILE = "chrome116"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)


def extract_recording_id_from_url(url):
    """Extract recording ID from Zoom URL"""
    parsed = urlparse(url)
    path_parts = parsed.path.split('/')
    
    # Try different URL patterns
    if 'rec' in path_parts and 'share' in path_parts:
        # Pattern: /rec/share/{recording_id}
        idx = path_parts.index('share')
        if idx + 1 < len(path_parts):
            return path_parts[idx + 1].split('?')[0]
    
    return None


def save_variables(variables, output_dir):
    """Save extracted variables to files"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as JSON
    json_file = os.path.join(output_dir, f"zoom_recording_vars_{timestamp}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(variables, f, indent=2, ensure_ascii=False)
    
    # Save as Python config
    py_file = os.path.join(output_dir, "zoom_config.py")
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write('"""Zoom Recording Configuration"""\n\n')
        for key, value in variables.items():
            if isinstance(value, str):
                f.write(f'{key} = "{value}"\n')
    
    return json_file, py_file
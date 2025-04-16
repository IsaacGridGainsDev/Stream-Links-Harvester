"""
Configuration management for the link harvester.
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class Config:
    """Configuration settings for the link harvester."""
    
    # Browser and request settings
    delay_between_requests: int = 5
    max_requests_per_minute: int = 10
    timeout: int = 15
    
    # Output settings
    output_dir: str = "./out"
    idm_path: str = "C:/Program Files (x86)/Internet Download Manager/IDMan.exe"
    download_dir: str = "C:/Downloads"
    
    # Selector settings - these could be customized for different sites
    download_link_selector: str = "a.download-button, a[data-download], a.video-download, a[href*='download']"
    # Additional selectors might be added based on site-specific requirements
    
    # XHR intercept patterns - URLs patterns to watch for video manifests
    xhr_patterns: list = None
    
    def __post_init__(self):
        """Initialize default values that require processing."""
        if self.xhr_patterns is None:
            self.xhr_patterns = [
                "*.m3u8*",  # HLS manifests
                "*.mpd*",   # DASH manifests
                "*video*",  # Common pattern in video URLs
                "*media*",  # Common pattern in media URLs
                "*stream*"  # Common pattern in streaming URLs
            ]


def load_config(config_path: str) -> Config:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Config object with settings from the file
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as file:
        config_data = yaml.safe_load(file)
    
    # Create a default config
    config = Config()
    
    # Update with values from the file
    if config_data:
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    return config


def write_default_config(output_path: str) -> None:
    """
    Write a default configuration file.
    
    Args:
        output_path: Path to write the default configuration file
    """
    config = Config()
    config_dict = {
        key: value for key, value in config.__dict__.items()
    }
    
    with open(output_path, 'w') as file:
        yaml.dump(config_dict, file, default_flow_style=False)

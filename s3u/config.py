"""
Configuration management for s3u utility.

This module provides functionality to read, write, and manage persistent
configuration settings for the s3u utility.
"""

import os
import json
import sys
from pathlib import Path

try:
    import questionary
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False

# Define config file location in the user's home directory
CONFIG_DIR = os.path.join(str(Path.home()), '.s3u')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

# Default configuration settings
DEFAULT_CONFIG = {
    "format": "array",
    "concurrent": 5,
    "optimize": "auto",
    "size": "optimized",
    "rename_mode": "replace",
    "image_format": "webp",     # Default image format (webp, jpg, avif)
    "video_format": "mp4",      # Default video format (mp4, webm)
    "optimize_videos": "no",    # Whether to transcode videos
    "video_preset": "medium",   # Video encoding preset
    "max_workers": 4,           # Maximum number of concurrent optimization workers
    "remove_audio": "no",       # Whether to remove audio from videos (for pATCHES mode)
    "subfolder_mode": "ignore",  # How to handle subfolders when uploading
    
    "aws_profile": "",  # Blank means default profile
    "bucket_name": "",  # Will prompt on first run
    "cloudfront_url": "",
    "region": "",
    "setup_complete": False  # Flag to track if setup has run
}

# Configuration options and their allowed values
CONFIG_OPTIONS = {
    "format": {
        "description": "Output format for generated URLs",
        "values": ["array", "json", "xml", "html", "csv"],
        "default": "array"
    },
    "concurrent": {
        "description": "Default number of concurrent uploads",
        "values": list(range(1, 21)),  # 1-20
        "default": 5
    },
    "optimize": {
        "description": "Default image optimization setting",
        "values": ["auto", "always", "never"],
        "default": "auto"
    },
    "size": {
        "description": "Default optimization size",
        "values": ["optimized", "small", "tiny"],
        "default": "optimized"
    },
    "rename_mode": {
        "description": "How to apply the rename prefix to filenames",
        "values": ["replace", "prepend", "append"],
        "default": "replace"
    },
    "image_format": {
        "description": "Default image output format",
        "values": ["webp", "jpg", "avif"],
        "default": "webp"
    },
    "remove_audio": {
        "description": "Whether to remove audio from videos (pATCHES mode)",
        "values": ["yes", "no"],
        "default": "no"
    },
    "video_format": {
        "description": "Default video output format",
        "values": ["mp4", "webm"],
        "default": "mp4"
    },
    "optimize_videos": {
        "description": "Whether to transcode videos by default",
        "values": ["yes", "no"],
        "default": "no"
    },
    "video_preset": {
        "description": "Video encoding preset (faster vs smaller files)",
        "values": ["fast", "medium", "slow"],
        "default": "medium"
    },
    "max_workers": {
        "description": "Maximum number of parallel optimization workers",
        "values": list(range(1, 17)),  # 1-16 workers
        "default": 4
    },
    "subfolder_mode": {
    "description": "How to handle subfolders when uploading",
    "values": ["ignore", "pool", "preserve"],
    "default": "ignore"
},
        "aws_profile": {
        "description": "AWS profile to use (leave blank for default)",
        "values": [],  # Will be populated with available profiles
        "default": ""
    },
    "bucket_name": {
        "description": "S3 bucket for uploads and downloads",
        "values": [],  # Will be populated dynamically
        "default": ""
    },
    "cloudfront_url": {
        "description": "CloudFront distribution URL",
        "values": [],
        "default": ""
    }
}

def ensure_config_dir():
    """Ensure that the config directory exists."""
    os.makedirs(CONFIG_DIR, exist_ok=True)

def load_config():
    """
    Load configuration from the config file.
    If the file doesn't exist, create it with default values.
    
    Returns:
        dict: The configuration dictionary
    """
    ensure_config_dir()
    
    if not os.path.exists(CONFIG_FILE):
        # Create default config file if it doesn't exist
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
        # Ensure all expected keys are present
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
                
        return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading config: {str(e)}")
        print("Using default configuration")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to config file."""
    config_dir = os.path.expanduser("~/.s3u")
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, "config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

def get_config_value(key, default=None):
    """
    Get a configuration value by key.
    
    Args:
        key (str): The configuration key
        default: Default value if the key is not found
        
    Returns:
        The configuration value, or default if not found
    """
    config = load_config()
    return config.get(key, default)

def set_config_value(key, value):
    """
    Set a configuration value.
    
    Args:
        key (str): The configuration key
        value: The value to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = load_config()
    config[key] = value
    return save_config(config)

def validate_option(option, value):
    """
    Validate that an option and value are valid.
    
    Args:
        option (str): The option key
        value: The option value
        
    Returns:
        tuple: (is_valid, message)
    """
    if option not in CONFIG_OPTIONS:
        return False, f"Unknown option: {option}"
    
    # Handle special case for numeric values
    if option == "concurrent":
        try:
            num_value = int(value)
            if num_value in CONFIG_OPTIONS[option]["values"]:
                return True, f"Set {option} to {num_value}"
            else:
                return False, f"Value for {option} must be between 1 and 20"
        except ValueError:
            return False, f"Value for {option} must be an integer"
    
    # For string options, convert to lowercase for case-insensitive comparison
    if isinstance(value, str):
        value_lower = value.lower()
        allowed_values = [str(v).lower() for v in CONFIG_OPTIONS[option]["values"]]
        
        if value_lower in allowed_values:
            # Return the properly cased version if it's a string
            proper_value = CONFIG_OPTIONS[option]["values"][allowed_values.index(value_lower)]
            return True, f"Set {option} to {proper_value}"
        else:
            return False, f"Invalid value for {option}. Allowed values: {', '.join(str(v) for v in CONFIG_OPTIONS[option]['values'])}"
    
    return False, f"Invalid value type for {option}"

def configure_option(option, value=None):
    """
    Configure a specific option, either interactively or with a provided value.
    
    Args:
        option (str): The option to configure
        value: The value to set (if None, prompt interactively)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if option not in CONFIG_OPTIONS:
        print(f"Unknown option: {option}")
        print(f"Available options: {', '.join(CONFIG_OPTIONS.keys())}")
        return False
    
    config = load_config()
    current_value = config.get(option, CONFIG_OPTIONS[option]["default"])
    
    if value is not None:
        # Direct configuration
        is_valid, message = validate_option(option, value)
        if is_valid:
            # Get the proper case for string values
            if option == "concurrent":
                proper_value = int(value)
            else:
                value_lower = value.lower()
                allowed_values = [str(v).lower() for v in CONFIG_OPTIONS[option]["values"]]
                proper_value = CONFIG_OPTIONS[option]["values"][allowed_values.index(value_lower)]
            
            config[option] = proper_value
            save_config(config)
            print(message)
            return True
        else:
            print(message)
            return False
    
    # Interactive configuration
    print(f"\nConfiguring: {option}")
    print(f"Description: {CONFIG_OPTIONS[option]['description']}")
    print(f"Current value: {current_value}")
    
    # Use arrow keys if questionary is available, otherwise fall back to text input
    if option == "concurrent":
        # For numeric options, always use text input
        while True:
            user_input = input(f"Enter new value (1-20) [{current_value}]: ").strip()
            if not user_input:
                return False  # Keep current value
            
            try:
                value = int(user_input)
                if value in CONFIG_OPTIONS[option]["values"]:
                    config[option] = value
                    save_config(config)
                    print(f"Set {option} to {value}")
                    return True
                else:
                    print(f"Value must be between 1 and 20")
            except ValueError:
                print("Please enter a valid integer")
    else:
        # For string options, use questionary if available
        if QUESTIONARY_AVAILABLE:
            # Find the index of the current value
            allowed_values = CONFIG_OPTIONS[option]["values"]
            try:
                default_index = allowed_values.index(current_value)
            except ValueError:
                default_index = 0  # Default to first option if not found
                
            # Use questionary select
            print("Use arrow keys to select an option, Enter to confirm:")
            choice = questionary.select(
                "Select value:",
                choices=allowed_values,
                default=allowed_values[default_index]
            ).ask()
            
            if choice:
                config[option] = choice
                save_config(config)
                print(f"Set {option} to {choice}")
                return True
            return False
        else:
            # Fall back to text input
            print(f"Allowed values: {', '.join(str(v) for v in CONFIG_OPTIONS[option]['values'])}")
            while True:
                user_input = input(f"Enter new value [{current_value}]: ").strip()
                if not user_input:
                    return False  # Keep current value
                
                is_valid, message = validate_option(option, user_input)
                if is_valid:
                    # Get the proper case
                    user_input_lower = user_input.lower()
                    allowed_values = [str(v).lower() for v in CONFIG_OPTIONS[option]["values"]]
                    proper_value = CONFIG_OPTIONS[option]["values"][allowed_values.index(user_input_lower)]
                    
                    config[option] = proper_value
                    save_config(config)
                    print(message)
                    return True
                else:
                    print(message)

def show_config():
    """Display the current configuration."""
    config = load_config()
    
    print("\nCurrent Configuration:")
    print("---------------------")
    for key, value in sorted(config.items()):
        if key in CONFIG_OPTIONS:
            print(f"{key}: {value} - {CONFIG_OPTIONS[key]['description']}")
        else:
            print(f"{key}: {value}")
    print("---------------------")

def handle_config_command(args):
    """
    Handle the -config command.
    
    Args:
        args (list): Command line arguments following -config
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not args:
        # No arguments, show the current configuration
        show_config()
        return True
    
    option = args[0].lower()
    
    if option == "show":
        # Show the current configuration
        show_config()
        return True
    
    if option not in CONFIG_OPTIONS:
        print(f"Unknown option: {option}")
        print(f"Available options: {', '.join(CONFIG_OPTIONS.keys())}")
        return False
    
    if len(args) > 1:
        # Direct configuration: -config option value
        return configure_option(option, args[1])
    else:
        # Interactive configuration: -config option
        return configure_option(option)
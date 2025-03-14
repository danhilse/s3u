# s3u package
__version__ = '0.2.0'

# Import and export key functions for backwards compatibility
from .core import (
    # Core S3 Operations
    check_folder_exists,
    ensure_s3_folder_exists,
    
    # Uploader
    upload_files,
    upload_file,
    rename_files,
    should_process_file,
    
    # Downloader
    download_folder,
    
    # Browser
    list_folders,
    list_s3_folder_objects,
    
    # Formatter
    format_output
)

# Import and export config functions
from .config import (
    load_config,
    save_config,
    get_config_value,
    set_config_value,
    handle_config_command,
    show_config
)

# Import and export optimizer functions
from .optimizer import process_directory
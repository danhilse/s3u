"""
Core S3 operations for the s3u utility.
"""

# Import and expose key functions from the modules
from .s3_core import (
    check_folder_exists,
    ensure_s3_folder_exists,
    get_s3_session
)

from .uploader import (
    upload_files,
    upload_file,
    rename_files,
    should_process_file
)

from .downloader import (
    download_folder,
    download_file
)

from .browser import (
    list_folders,
    list_s3_folder_objects
)

from .formatter import (
    format_output,
    format_array,
    format_json,
    format_xml,
    format_html,
    format_csv
)
"""
File upload functionality for S3.
"""

import os
import sys
import asyncio
import pyperclip
from datetime import datetime
from botocore.exceptions import NoCredentialsError

from .s3_core import get_s3_session, BUCKET_NAME, CLOUDFRONT_URL, ensure_s3_folder_exists
from .formatter import format_output
from .browser import list_s3_folder_objects

def should_process_file(filename, extensions):
    """
    Check if a file should be processed based on its extension.
    
    Args:
        filename (str): The filename to check
        extensions (list): List of extensions to include
        
    Returns:
        bool: True if the file should be processed, False otherwise
    """
    if not extensions:  # If no extensions specified, process all files except hidden ones
        return not filename.startswith('.') and filename != '.DS_Store'
    
    # Check if file has one of the specified extensions
    file_lower = filename.lower()
    
    for ext in extensions:
        ext_lower = ext.lower()
        
        # Special case for jpg to also include jpeg
        if ext_lower == 'jpg':
            if file_lower.endswith('.jpg') or file_lower.endswith('.jpeg'):
                return True
        # Special case for mp4 and mov
        elif ext_lower == 'mp4':
            if file_lower.endswith('.mp4'):
                return True
        elif ext_lower == 'mov':
            if file_lower.endswith('.mov'):
                return True
        # All other extensions
        else:
            if file_lower.endswith(f".{ext_lower}"):
                return True
    
    return False

def rename_files(directory, extensions, rename_prefix=None, rename_mode='replace', specific_files=None):
    """
    Rename files with a common prefix and sequential numbering.
    
    Args:
        directory (str): The directory containing files
        extensions (list): List of extensions to include
        rename_prefix (str): Optional prefix for renamed files
        rename_mode (str): Rename mode - 'replace', 'prepend', or 'append'
        specific_files (list): Optional list of specific files to rename
        
    Returns:
        tuple: (renamed_files, original_to_new)
    """
    if specific_files:
        # Use the specific files provided instead of searching the directory
        files = [os.path.basename(f) for f in specific_files]
        file_paths = specific_files
    else:
        # Use files from the directory filtered by extension
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and should_process_file(f, extensions)]
        file_paths = [os.path.join(directory, f) for f in files]
    
    if not files:
        print(f"WARNING: No matching files found in directory with extensions: {extensions}")
        if not specific_files:
            print(f"Files in directory: {os.listdir(directory)}")
        return [], {}
        
    files.sort()
    file_paths.sort()
    print(f"Found {len(files)} matching files to upload")
    
    renamed_files = []
    original_to_new = {}
    
    if rename_prefix:
        # Calculate number of digits needed based on total files
        num_files = len(files)
        if num_files <= 9:
            digits = 1
        elif num_files <= 99:
            digits = 2
        elif num_files <= 999:
            digits = 3
        else:  # Cap at 4 digits
            digits = 4
            
        # Format string for the index with leading zeros
        format_str = f"{{0:0{digits}d}}"
        
        for i, (filename, filepath) in enumerate(zip(files, file_paths), start=1):
            name, ext = os.path.splitext(filename)
            index_str = format_str.format(i)
            
            # Apply the rename based on the mode
            if rename_mode == 'replace':
                new_name = f"{rename_prefix}_{index_str}{ext}"
            elif rename_mode == 'prepend':
                new_name = f"{rename_prefix}_{name}{ext}"
            elif rename_mode == 'append':
                new_name = f"{name}_{rename_prefix}{ext}"
            else:
                # Default to replace mode if invalid mode is specified
                new_name = f"{rename_prefix}_{index_str}{ext}"
            
            new_path = os.path.join(directory, new_name)
            os.rename(filepath, new_path)
            renamed_files.append(new_path)
            original_to_new[filename] = new_name
            print(f"Renamed: {filepath} -> {new_path}")
    else:
        # Keep original filenames
        renamed_files = file_paths
        for f in files:
            original_to_new[f] = f
        print("Using original filenames")
    
    return renamed_files, original_to_new

async def upload_files(s3_folder, extensions=None, rename_prefix=None, rename_mode='replace',
                      only_first=False, max_concurrent=10, source_dir='.', specific_files=None, 
                      include_existing=True, output_format='array'):
    """
    Upload files from the specified directory to S3.
    
    Args:
        s3_folder (str): The folder name in the S3 bucket to upload to
        extensions (list): File extensions to include (e.g., ['jpg', 'png'])
        rename_prefix (str): Prefix for renaming files before upload
        rename_mode (str): How to apply the rename prefix ('replace', 'prepend', 'append')
        only_first (bool): Only copy the first URL to clipboard
        max_concurrent (int): Maximum concurrent uploads
        source_dir (str): Directory containing files to upload
        specific_files (list): Optional list of specific files to upload
        include_existing (bool): Whether to include existing files in the CDN links
        output_format (str): Format for output: 'array', 'json', 'xml', 'html', or 'csv'
    
    Returns:
        list: List of CloudFront URLs for uploaded files
    """
    session = get_s3_session()
    
    # Ensure S3 folder exists
    await ensure_s3_folder_exists(session, s3_folder)
    
    # Rename files
    renamed_files, original_to_new = rename_files(source_dir, extensions, rename_prefix, rename_mode, specific_files)
    
    if not renamed_files:
        print("No files to upload.")
        return []
    
    # Create a semaphore to limit concurrent uploads
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def upload_with_semaphore(file):
        async with semaphore:
            return await upload_file(session, file, s3_folder)
    
    # Create tasks for all file uploads
    tasks = [upload_with_semaphore(file) for file in renamed_files]
    
    # Progress tracking
    total_files = len(tasks)
    print(f"Starting upload of {total_files} files...")
    
    # Wait for all uploads to complete
    results = await asyncio.gather(*tasks)
    
    # Extract successful upload URLs and metadata
    uploaded_urls = []
    uploaded_objects = []
    
    for success, data in results:
        if success and data:
            uploaded_urls.append(data['url'])
            uploaded_objects.append(data)
    
    print(f"\nCompleted {len(uploaded_urls)} of {total_files} uploads")
    
    # Get existing files if needed
    if include_existing:
        print("Including existing files in the CDN links...")
        if output_format == 'array':
            existing_urls = await list_s3_folder_objects(s3_folder, return_urls_only=True)
            # Merge the lists, ensuring no duplicates by converting to a set first
            all_urls = list(set(uploaded_urls + existing_urls))
            print(f"Total of {len(all_urls)} files in folder (new + existing)")
            all_objects = []  # We don't need objects for array format
        else:
            existing_objects = await list_s3_folder_objects(s3_folder, return_urls_only=False, output_format='json')
            
            # Create a set of uploaded URLs for faster lookup
            uploaded_url_set = set(uploaded_urls)
            
            # Filter existing objects to avoid duplicates
            filtered_existing = [obj for obj in existing_objects if obj['url'] not in uploaded_url_set]
            
            # Merge the lists
            all_objects = uploaded_objects + filtered_existing
            all_urls = [obj['url'] for obj in all_objects]
            
            print(f"Total of {len(all_urls)} files in folder (new + existing)")
    else:
        all_urls = uploaded_urls
        all_objects = uploaded_objects
        print(f"Including only newly uploaded files ({len(all_urls)})")
    
    # Copy to clipboard
    if all_urls:
        if only_first and output_format == 'array':
            pyperclip.copy(all_urls[0])
            print(f"\nCopied first URL to clipboard: {all_urls[0]}")
        else:
            clipboard_content = format_output(all_urls, all_objects, output_format)
            pyperclip.copy(clipboard_content)
            print(f"\nCopied {output_format} format data to clipboard")
    
    return all_urls

async def upload_files(s3_folder, extensions=None, rename_prefix=None, only_first=False, 
                       max_concurrent=10, source_dir='.', specific_files=None, 
                       include_existing=True, output_format='array'):
    """
    Upload files from the specified directory to S3.
    
    Args:
        s3_folder (str): The folder name in the S3 bucket to upload to
        extensions (list): File extensions to include (e.g., ['jpg', 'png'])
        rename_prefix (str): Prefix for renaming files before upload
        only_first (bool): Only copy the first URL to clipboard
        max_concurrent (int): Maximum concurrent uploads
        source_dir (str): Directory containing files to upload
        specific_files (list): Optional list of specific files to upload
        include_existing (bool): Whether to include existing files in the CDN links
        output_format (str): Format for output: 'array', 'json', 'xml', 'html', or 'csv'
    
    Returns:
        list: List of CloudFront URLs for uploaded files
    """
    session = get_s3_session()
    
    # Ensure S3 folder exists
    await ensure_s3_folder_exists(session, s3_folder)
    
    # Rename files
    renamed_files, original_to_new = rename_files(source_dir, extensions, rename_prefix, specific_files)
    
    if not renamed_files:
        print("No files to upload.")
        return []
    
    # Create a semaphore to limit concurrent uploads
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def upload_with_semaphore(file):
        async with semaphore:
            return await upload_file(session, file, s3_folder)
    
    # Create tasks for all file uploads
    tasks = [upload_with_semaphore(file) for file in renamed_files]
    
    # Progress tracking
    total_files = len(tasks)
    print(f"Starting upload of {total_files} files...")
    
    # Wait for all uploads to complete
    results = await asyncio.gather(*tasks)
    
    # Extract successful upload URLs and metadata
    uploaded_urls = []
    uploaded_objects = []
    
    for success, data in results:
        if success and data:
            uploaded_urls.append(data['url'])
            uploaded_objects.append(data)
    
    print(f"\nCompleted {len(uploaded_urls)} of {total_files} uploads")
    
    # Get existing files if needed
    if include_existing:
        print("Including existing files in the CDN links...")
        if output_format == 'array':
            existing_urls = await list_s3_folder_objects(s3_folder, return_urls_only=True)
            # Merge the lists, ensuring no duplicates by converting to a set first
            all_urls = list(set(uploaded_urls + existing_urls))
            print(f"Total of {len(all_urls)} files in folder (new + existing)")
            all_objects = []  # We don't need objects for array format
        else:
            existing_objects = await list_s3_folder_objects(s3_folder, return_urls_only=True, output_format='json')
            
            # Create a set of uploaded URLs for faster lookup
            uploaded_url_set = set(uploaded_urls)
            
            # Filter existing objects to avoid duplicates
            filtered_existing = [obj for obj in existing_objects if obj['url'] not in uploaded_url_set]
            
            # Merge the lists
            all_objects = uploaded_objects + filtered_existing
            all_urls = [obj['url'] for obj in all_objects]
            
            print(f"Total of {len(all_urls)} files in folder (new + existing)")
    else:
        all_urls = uploaded_urls
        all_objects = uploaded_objects
        print(f"Including only newly uploaded files ({len(all_urls)})")
    
    # Copy to clipboard
    if all_urls:
        if only_first and output_format == 'array':
            pyperclip.copy(all_urls[0])
            print(f"\nCopied first URL to clipboard: {all_urls[0]}")
        else:
            clipboard_content = format_output(all_urls, all_objects, output_format)
            pyperclip.copy(clipboard_content)
            print(f"\nCopied {output_format} format data to clipboard")
    
    return all_urls
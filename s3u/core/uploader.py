"""
File upload functionality for S3.
"""

import os
import sys
import asyncio
import pyperclip
from datetime import datetime
from botocore.exceptions import NoCredentialsError

from .s3_core import get_s3_session, get_bucket_name, get_cloudfront_url, ensure_s3_folder_exists
from .formatter import format_output

# Remove the circular import between browser.py and uploader.py
# This function will be used to get existing files

async def list_s3_folder_objects_internal(s3_folder, return_urls_only=False, limit=None, output_format='array', recursive=False):
    """
    List objects in an S3 folder and return their CloudFront URLs.
    This is an internal version to avoid circular imports.
    For full functionality, use the version in browser.py.
    
    Args:
        s3_folder (str): The folder name in the S3 bucket to list
        return_urls_only (bool): If True, just return the URLs without printing or clipboard copy
        limit (int): Optional limit on the number of URLs to return
        output_format (str): Format for output: 'array', 'json', 'xml', 'html', or 'csv'
        recursive (bool): Whether to list objects recursively including subfolders
        
    Returns:
        list: List of CloudFront URLs or objects with metadata for items in the folder
    """
    session = get_s3_session()
    urls = []
    objects = []
    
    try:
        async with session.client('s3') as s3:
            paginator = s3.get_paginator('list_objects_v2')
            
            # Add trailing slash if not present to ensure we're listing folder contents
            folder_prefix = s3_folder if s3_folder.endswith('/') else f"{s3_folder}/"
            
            if recursive:
                # List all objects recursively (no delimiter)
                async for page in paginator.paginate(Bucket=get_bucket_name(), Prefix=folder_prefix):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            # Skip the folder itself and any subfolder markers
                            if obj['Key'] != folder_prefix and not obj['Key'].endswith('/'):
                                url = f"{get_cloudfront_url()}/{obj['Key']}"
                                urls.append(url)
                                
                                # Collect metadata for formats that need it
                                if output_format != 'array':
                                    obj_meta = {
                                        'url': url,
                                        'filename': os.path.basename(obj['Key']),
                                        's3_path': obj['Key'],
                                        'size': obj['Size'],
                                        'last_modified': obj['LastModified'].isoformat(),
                                        'type': os.path.splitext(obj['Key'])[1].lstrip('.').lower() if '.' in obj['Key'] else '',
                                        'subfolder': os.path.dirname(obj['Key'].replace(folder_prefix, '')) if '/' in obj['Key'].replace(folder_prefix, '') else ''
                                    }
                                    objects.append(obj_meta)
            else:
                # List only objects in the specific folder (using delimiter)
                async for page in paginator.paginate(Bucket=get_bucket_name(), Prefix=folder_prefix, Delimiter='/'):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            # Skip the folder itself (which appears as a key)
                            if obj['Key'] != folder_prefix:
                                url = f"{get_cloudfront_url()}/{obj['Key']}"
                                urls.append(url)
                                
                                # Collect metadata for formats that need it
                                if output_format != 'array':
                                    obj_meta = {
                                        'url': url,
                                        'filename': os.path.basename(obj['Key']),
                                        's3_path': obj['Key'],
                                        'size': obj['Size'],
                                        'last_modified': obj['LastModified'].isoformat(),
                                        'type': os.path.splitext(obj['Key'])[1].lstrip('.').lower() if '.' in obj['Key'] else ''
                                    }
                                    objects.append(obj_meta)
            
            # Sort the URLs alphabetically for consistent results when limiting
            urls.sort()
            if objects:
                objects.sort(key=lambda x: x['s3_path'])
            
            # Apply limit if specified
            if limit and limit > 0:
                if limit < len(urls):
                    urls = urls[:limit]
                if objects and limit < len(objects):
                    objects = objects[:limit]
            
            return urls if output_format == 'array' or return_urls_only else objects
    except NoCredentialsError:
        print("Credentials not available")
        sys.exit(1)
    except Exception as e:
        print(f"Error listing objects in folder {s3_folder}: {str(e)}")
        return []

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

async def upload_file(session, file_path, s3_folder):
    """
    Upload a single file to S3.
    
    Args:
        session (aioboto3.Session): aioboto3 session
        file_path (str): Path to the file to upload
        s3_folder (str): Destination folder in S3
        
    Returns:
        tuple: (success, data) where data contains URL and metadata if successful
    """
    try:
        # Get file properties
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_type = get_mime_type(file_path)
        
        # Generate S3 key with folder prefix
        s3_key = f"{s3_folder}/{file_name}" if s3_folder else file_name
        
        # Get file timestamp
        timestamp = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        # Prepare progress callback
        file_progress = {
            'uploaded': 0,
            'total': file_size,
            'start_time': None
        }
        
        def progress_callback(bytes_transferred):
            if file_progress['start_time'] is None:
                file_progress['start_time'] = datetime.now()
            
            file_progress['uploaded'] = bytes_transferred
            percent = (bytes_transferred / file_size) * 100
            
            # Calculate ETA
            if bytes_transferred > 0:
                elapsed_time = (datetime.now() - file_progress['start_time']).total_seconds()
                upload_speed = bytes_transferred / elapsed_time if elapsed_time > 0 else 0
                remaining_bytes = file_size - bytes_transferred
                eta_seconds = remaining_bytes / upload_speed if upload_speed > 0 else 0
                
                # Format ETA
                eta = ""
                if eta_seconds < 60:
                    eta = f"{eta_seconds:.0f}s"
                else:
                    eta = f"{eta_seconds/60:.1f}m"
                
                # Format speed
                speed = ""
                if upload_speed < 1024:
                    speed = f"{upload_speed:.2f} B/s"
                elif upload_speed < 1024 * 1024:
                    speed = f"{upload_speed/1024:.2f} KB/s"
                else:
                    speed = f"{upload_speed/(1024*1024):.2f} MB/s"
                
                sys.stdout.write(f"\rUploading {file_name}: {percent:.1f}% | {speed} | ETA: {eta}")
            else:
                sys.stdout.write(f"\rUploading {file_name}: {percent:.1f}%")
            
            sys.stdout.flush()
        
        # Use the async context manager to get the client
        async with session.client('s3') as s3:
            # Perform the upload with progress callback, without ACL setting
            with open(file_path, 'rb') as f:
                await s3.upload_fileobj(
                    f, 
                    get_bucket_name(), 
                    s3_key,
                    Callback=progress_callback,
                    ExtraArgs={
                        'ContentType': file_type
                        # Removed 'ACL': 'public-read' to work with limited permissions
                    }
                )
        
        # Print newline after progress
        print()
        
        # Generate CloudFront URL for the file
        cloudfront_url = f"{get_cloudfront_url()}/{s3_key}"
        
        # Return success with URL and metadata
        return True, {
            'url': cloudfront_url,
            'key': s3_key,
            'size': file_size,
            'type': file_type,
            'timestamp': timestamp.isoformat(),
            'bucket': get_bucket_name()
        }
    
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return False, None
    except NoCredentialsError:
        print("Error: AWS credentials not found")
        return False, None
    except Exception as e:
        print(f"Error uploading {file_path}: {str(e)}")
        return False, None
    
def get_mime_type(file_path):
    """
    Get the MIME type of a file based on its extension.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: MIME type string
    """
    # Map of common extensions to MIME types
    extension_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.avif': 'image/avif',
        '.mp4': 'video/mp4',
        '.mov': 'video/quicktime',
        '.webm': 'video/webm',
        '.txt': 'text/plain',
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.pdf': 'application/pdf',
        '.zip': 'application/zip'
    }
    
    # Get the file extension
    _, ext = os.path.splitext(file_path.lower())
    
    # Return the mapped MIME type or a default
    return extension_map.get(ext, 'application/octet-stream')

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
                      include_existing=True, output_format='array', subfolder_mode='ignore'):
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
        subfolder_mode (str): How to handle subfolders: 'ignore', 'pool', or 'preserve'
    
    Returns:
        list: List of CloudFront URLs for uploaded files
    """
    session = get_s3_session()
    
    # Ensure S3 folder exists
    await ensure_s3_folder_exists(session, s3_folder)
    
    # Handle files based on subfolder mode
    if subfolder_mode == 'ignore' or specific_files:
        # Use the existing logic for specific_files or just the main directory
        renamed_files, original_to_new = rename_files(source_dir, extensions, rename_prefix, rename_mode, specific_files)
    else:
        # We need to handle subfolders
        all_files = []
        
        if subfolder_mode == 'pool':
            # Pool all files from subfolders into one list
            for root, _, files in os.walk(source_dir):
                for file in files:
                    if should_process_file(file, extensions):
                        all_files.append(os.path.join(root, file))
            
            # Rename all files together
            renamed_files, original_to_new = rename_files(
                source_dir, 
                extensions, 
                rename_prefix, 
                rename_mode, 
                specific_files=all_files
            )
        elif subfolder_mode == 'preserve':
            # Preserve the subfolder structure
            renamed_files = []
            original_to_new = {}
            
            for root, _, files in os.walk(source_dir):
                subfolder_files = [os.path.join(root, f) for f in files if should_process_file(f, extensions)]
                
                if subfolder_files:
                    # Get relative path for the subfolder
                    rel_path = os.path.relpath(root, source_dir)
                    
                    # Skip the main directory
                    if rel_path == '.':
                        subfolder_renamed, subfolder_map = rename_files(
                            root, 
                            extensions, 
                            rename_prefix, 
                            rename_mode
                        )
                    else:
                        # For subfolders, use the subfolder path for uploads
                        subfolder_renamed, subfolder_map = rename_files(
                            root, 
                            extensions, 
                            rename_prefix, 
                            rename_mode
                        )
                    
                    renamed_files.extend(subfolder_renamed)
                    original_to_new.update(subfolder_map)
    
    if not renamed_files:
        print("No files to upload.")
        return []
    
    # Create a semaphore to limit concurrent uploads
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def upload_with_semaphore(file):
        async with semaphore:
            # Determine the S3 subfolder based on the file's location
            if subfolder_mode == 'preserve' and not specific_files:
                rel_path = os.path.relpath(os.path.dirname(file), source_dir)
                
                if rel_path == '.':
                    # File is in the main directory
                    target_folder = s3_folder
                else:
                    # File is in a subfolder
                    target_folder = f"{s3_folder}/{rel_path}"
                    # Ensure the subfolder exists in S3
                    await ensure_s3_folder_exists(session, target_folder)
            else:
                # For 'ignore' or 'pool' modes, use the main folder
                target_folder = s3_folder
            
            return await upload_file(session, file, target_folder)
    
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
            existing_urls = await list_s3_folder_objects_internal(s3_folder, return_urls_only=True, recursive=(subfolder_mode == 'preserve'))
            # Merge the lists, ensuring no duplicates by converting to a set first
            all_urls = list(set(uploaded_urls + existing_urls))
            print(f"Total of {len(all_urls)} files in folder (new + existing)")
            all_objects = []  # We don't need objects for array format
        else:
            existing_objects = await list_s3_folder_objects_internal(s3_folder, return_urls_only=False, output_format='json', recursive=(subfolder_mode == 'preserve'))
            
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
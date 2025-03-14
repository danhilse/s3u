"""
File and folder download functionality.
"""

import os
import sys
import asyncio
from botocore.exceptions import NoCredentialsError

from .s3_core import get_s3_session, get_bucket_name
from ..utils.progress import ProgressBar

async def download_file(s3, file_key, output_dir, semaphore, progress, progress_lock):
    """
    Download a single file from S3.
    
    Args:
        s3: S3 client
        file_key (str): S3 object key
        output_dir (str): Local directory to save to
        semaphore: Asyncio semaphore for concurrency control
        progress: Progress bar object
        progress_lock: Asyncio lock for progress updates
        
    Returns:
        bool: True if successful, False otherwise
    """
    async with semaphore:
        try:
            # Extract folder prefix
            if '/' in file_key:
                folder_prefix = file_key.split('/')[0] + '/'
                relative_path = file_key[len(folder_prefix):]
            else:
                relative_path = file_key
                
            local_path = os.path.join(output_dir, relative_path)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download the file
            await s3.download_file(get_bucket_name(), file_key, local_path)
            
            # Update the progress bar
            async with progress_lock:
                file_size = os.path.getsize(local_path)
                progress.update(1)
            
            return True
        except Exception as e:
            print(f"\nError downloading {file_key}: {str(e)}")
            async with progress_lock:
                progress.update(1)
            return False

async def download_folder(folder_name, output_dir=None, limit=None):
    """
    Download files from an S3 folder.
    
    Args:
        folder_name (str): The folder to download
        output_dir (str): Local directory to save files (defaults to folder_name)
        limit (int): Optional limit on the number of files to download
        
    Returns:
        int: Number of files downloaded
    """
    session = get_s3_session()
    
    # Make sure folder name has trailing slash
    folder_prefix = folder_name if folder_name.endswith('/') else f"{folder_name}/"
    
    # Create local directory if it doesn't exist
    if not output_dir:
        output_dir = folder_name
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Get list of all objects in the folder
    files_to_download = []
    
    try:
        async with session.client('s3') as s3:
            paginator = s3.get_paginator('list_objects_v2')
            
            print(f"Scanning folder: {folder_name}")
            async for page in paginator.paginate(Bucket=get_bucket_name(), Prefix=folder_prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Skip the folder itself
                        if obj['Key'] != folder_prefix:
                            files_to_download.append(obj['Key'])
            
            if not files_to_download:
                print(f"No files found in folder: {folder_name}")
                return 0
            
            # Sort the files alphabetically for consistent results when limiting
            files_to_download.sort()
            
            # Apply limit if specified
            if limit and limit > 0 and limit < len(files_to_download):
                print(f"Limiting download to {limit} of {len(files_to_download)} files")
                files_to_download = files_to_download[:limit]
            
            print(f"Downloading {len(files_to_download)} files from {folder_name}")
            
            # Create a progress bar
            progress = ProgressBar(len(files_to_download), prefix=f'Downloading:', suffix='Complete')
            
            # Create a semaphore to limit concurrent downloads
            semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent downloads
            
            # Track progress
            progress_lock = asyncio.Lock()
            
            # Download all files concurrently
            tasks = [download_file(s3, file_key, output_dir, semaphore, progress, progress_lock) 
                    for file_key in files_to_download]
            results = await asyncio.gather(*tasks)
            
            successful_downloads = sum(1 for result in results if result)
            
            print(f"\nDownloaded {successful_downloads} of {len(files_to_download)} files to {output_dir}")
            
            return successful_downloads
    except NoCredentialsError:
        print("Credentials not available")
        sys.exit(1)
    except Exception as e:
        print(f"Error downloading folder {folder_name}: {str(e)}")
        return 0
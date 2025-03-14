import os
import sys
import asyncio
import aioboto3
import pyperclip
from botocore.exceptions import NoCredentialsError

BUCKET_NAME = "dh.images"
CLOUDFRONT_URL = "https://d1lbnboj0lfh6w.cloudfront.net"


class ProgressBar:
    """
    A simple progress bar for terminal output.
    """
    def __init__(self, total, prefix='Progress:', suffix='Complete', length=50, fill='█', print_end="\r"):
        """
        Initialize a progress bar.
        
        Args:
            total (int): Total items
            prefix (str): Prefix string
            suffix (str): Suffix string
            length (int): Bar length
            fill (str): Bar fill character
            print_end (str): End character (e.g. "\r", "\n")
        """
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.fill = fill
        self.print_end = print_end
        self.current = 0
        self.start_time = time.time()
        self._update_bar(0)
        
    def update(self, increment=1):
        """
        Update the progress bar.
        
        Args:
            increment (int): Increment progress by this amount
        """
        self.current += increment
        self._update_bar(self.current)
        
    def _update_bar(self, current):
        """
        Internal method to update the progress bar display.
        """
        percent = ("{0:.1f}").format(100 * (current / float(self.total)))
        filled_length = int(self.length * current // self.total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)
        
        # Calculate elapsed time and ETA
        elapsed = time.time() - self.start_time
        if current > 0:
            eta = elapsed * (self.total / current - 1)
            time_str = f"| {self._format_time(elapsed)} elapsed | ETA: {self._format_time(eta)}"
        else:
            time_str = ""
            
        # Print the bar
        print(f'\r{self.prefix} |{bar}| {percent}% {self.suffix} {time_str}', end=self.print_end)
        
        # Print a new line when complete
        if current == self.total:
            print()
            
    def _format_time(self, seconds):
        """Format time in a human-readable way."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds//60}m {seconds%60:.0f}s"
        else:
            return f"{seconds//3600}h {(seconds%3600)//60}m {seconds%3600%60:.0f}s"

def should_process_file(filename, extensions):
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

def rename_files(directory, extensions, rename_prefix=None, specific_files=None):
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

async def check_folder_exists(s3_folder):
    """
    Check if a folder already exists in the S3 bucket.
    
    Args:
        s3_folder (str): The folder name to check
        
    Returns:
        bool: True if the folder exists, False otherwise
    """
    session = aioboto3.Session()
    
    try:
        async with session.client('s3') as s3:
            # Add trailing slash if not present to ensure we're checking a folder
            folder_prefix = s3_folder if s3_folder.endswith('/') else f"{s3_folder}/"
            
            response = await s3.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=folder_prefix,
                MaxKeys=1
            )
            
            # If the folder exists, the response will contain 'Contents'
            return 'Contents' in response and len(response['Contents']) > 0
    except NoCredentialsError:
        print("Credentials not available")
        sys.exit(1)
    except Exception as e:
        print(f"Error checking if folder exists: {str(e)}")
        return False

async def ensure_s3_folder_exists(session, s3_folder):
    async with session.client('s3') as s3:
        try:
            await s3.put_object(Bucket=BUCKET_NAME, Key=(s3_folder + '/'))
            print(f"Ensured S3 folder exists: s3://{BUCKET_NAME}/{s3_folder}/")
        except NoCredentialsError:
            print("Credentials not available")
            sys.exit(1)

async def upload_file(session, local_file, s3_folder):
    s3_path = f"{s3_folder}/{os.path.basename(local_file)}" if s3_folder else os.path.basename(local_file)
    
    async with session.client('s3') as s3:
        try:
            await s3.upload_file(local_file, BUCKET_NAME, s3_path)
            url = f"{CLOUDFRONT_URL}/{s3_path}"
            print(f"Uploaded: {local_file} -> {url}")
            return True, url
        except FileNotFoundError:
            print(f"The file {local_file} was not found")
            return False, None
        except NoCredentialsError:
            print("Credentials not available")
            return False, None
        except Exception as e:
            print(f"Error uploading {local_file}: {str(e)}")
            return False, None


async def list_folders(prefix=""):
    """
    List all folders in the S3 bucket with item count.
    
    Args:
        prefix (str): Optional prefix to filter folders
        
    Returns:
        list: List of tuples containing (folder_name, item_count)
    """
    session = aioboto3.Session()
    folders = {}
    
    try:
        async with session.client('s3') as s3:
            paginator = s3.get_paginator('list_objects_v2')
            
            async for page in paginator.paginate(Bucket=BUCKET_NAME, Delimiter='/'):
                if 'CommonPrefixes' in page:
                    for prefix_obj in page['CommonPrefixes']:
                        folder_name = prefix_obj['Prefix'].rstrip('/')
                        folders[folder_name] = 0
            
            # Now count items in each folder
            for folder_name in folders.keys():
                folder_prefix = folder_name + '/'
                
                item_count = 0
                async for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=folder_prefix):
                    if 'Contents' in page:
                        # Don't count the folder marker itself
                        item_count += sum(1 for obj in page['Contents'] if obj['Key'] != folder_prefix)
                
                folders[folder_name] = item_count
            
            return [(folder, count) for folder, count in folders.items()]
    except NoCredentialsError:
        print("Credentials not available")
        sys.exit(1)
    except Exception as e:
        print(f"Error listing folders: {str(e)}")
        return []

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
    session = aioboto3.Session()
    
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
            async for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=folder_prefix):
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
            downloaded_bytes = 0
            progress_lock = asyncio.Lock()
            
            async def download_file(file_key):
                async with semaphore:
                    try:
                        # Extract the filename without the folder prefix
                        relative_path = file_key[len(folder_prefix):]
                        local_path = os.path.join(output_dir, relative_path)
                        
                        # Ensure the directory exists
                        os.makedirs(os.path.dirname(local_path), exist_ok=True)
                        
                        # Download the file
                        await s3.download_file(BUCKET_NAME, file_key, local_path)
                        
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
            
            # Download all files concurrently
            tasks = [download_file(file_key) for file_key in files_to_download]
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

async def list_s3_folder_objects(s3_folder, return_urls_only=False, limit=None):
    """
    List objects in an S3 folder and return their CloudFront URLs.
    
    Args:
        s3_folder (str): The folder name in the S3 bucket to list
        return_urls_only (bool): If True, just return the URLs without printing or clipboard copy
        limit (int): Optional limit on the number of URLs to return
        
    Returns:
        list: List of CloudFront URLs for objects in the folder
    """
    session = aioboto3.Session()
    urls = []
    
    try:
        async with session.client('s3') as s3:
            paginator = s3.get_paginator('list_objects_v2')
            
            # Add trailing slash if not present to ensure we're listing folder contents
            folder_prefix = s3_folder if s3_folder.endswith('/') else f"{s3_folder}/"
            
            async for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=folder_prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Skip the folder itself (which appears as a key)
                        if obj['Key'] != folder_prefix:
                            url = f"{CLOUDFRONT_URL}/{obj['Key']}"
                            urls.append(url)
            
            # Sort the URLs alphabetically for consistent results when limiting
            urls.sort()
            
            # Apply limit if specified
            if limit and limit > 0 and limit < len(urls):
                if not return_urls_only:
                    print(f"Limiting to {limit} of {len(urls)} URLs")
                urls = urls[:limit]
            
            if not return_urls_only:
                if not urls:
                    print(f"No objects found in folder: {s3_folder}")
                else:
                    print(f"Found {len(urls)} objects in folder: {s3_folder}")
                    
                    # Copy to clipboard
                    json_array = "[" + ", ".join([f'"{url}"' for url in urls]) + "]"
                    pyperclip.copy(json_array)
                    print(f"\nCopied JSON array of {len(urls)} URLs to clipboard")
                
            return urls
    except NoCredentialsError:
        print("Credentials not available")
        sys.exit(1)
    except Exception as e:
        print(f"Error listing objects in folder {s3_folder}: {str(e)}")
        return []

async def upload_files(s3_folder, extensions=None, rename_prefix=None, only_first=False, 
                       max_concurrent=10, source_dir='.', specific_files=None, 
                       include_existing=True):
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
    
    Returns:
        list: List of CloudFront URLs for uploaded files
    """
    session = aioboto3.Session()
    
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
    
    # Extract successful upload URLs
    uploaded_paths = [url for success, url in results if success and url]
    
    print(f"\nCompleted {len(uploaded_paths)} of {total_files} uploads")
    
    # Get existing files if needed
    if include_existing:
        print("Including existing files in the CDN links...")
        existing_paths = await list_s3_folder_objects(s3_folder, return_urls_only=True)
        # Merge the lists, ensuring no duplicates by converting to a set first
        all_paths = list(set(uploaded_paths + existing_paths))
        print(f"Total of {len(all_paths)} files in folder (new + existing)")
    else:
        all_paths = uploaded_paths
        print(f"Including only newly uploaded files ({len(all_paths)})")
    
    # Copy to clipboard
    if all_paths:
        if only_first:
            pyperclip.copy(all_paths[0])
            print(f"\nCopied first URL to clipboard: {all_paths[0]}")
        else:
            json_array = "[" + ", ".join([f'"{url}"' for url in all_paths]) + "]"
            pyperclip.copy(json_array)
            print(f"\nCopied JSON array of {len(all_paths)} URLs to clipboard")
    
    return all_paths
# S3 Upload Utility - New Features Implementation

This guide covers the implementation of two new features for the S3 Upload Utility:

1. Download folders with the `-d` flag
2. List all folders with the `-ls` flag

## 1. Folder Download Feature

### New Functions in `uploader.py`

Add the following function to download files from an S3 folder:

```python
async def download_folder(folder_name, output_dir=None):
    """
    Download all files from an S3 folder.
    
    Args:
        folder_name (str): The folder to download
        output_dir (str): Local directory to save files (defaults to folder_name)
        
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
            
            async for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=folder_prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Skip the folder itself
                        if obj['Key'] != folder_prefix:
                            files_to_download.append(obj['Key'])
            
            if not files_to_download:
                print(f"No files found in folder: {folder_name}")
                return 0
            
            print(f"Found {len(files_to_download)} files to download from {folder_name}")
            
            # Create a semaphore to limit concurrent downloads
            semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent downloads
            
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
                        print(f"Downloaded: {file_key} -> {local_path}")
                        return True
                    except Exception as e:
                        print(f"Error downloading {file_key}: {str(e)}")
                        return False
            
            # Download all files concurrently
            tasks = [download_file(file_key) for file_key in files_to_download]
            results = await asyncio.gather(*tasks)
            
            successful_downloads = sum(1 for result in results if result)
            print(f"Downloaded {successful_downloads} of {len(files_to_download)} files to {output_dir}")
            
            return successful_downloads
    except NoCredentialsError:
        print("Credentials not available")
        sys.exit(1)
    except Exception as e:
        print(f"Error downloading folder {folder_name}: {str(e)}")
        return 0
```

## 2. Folder Listing Feature

### New Function in `uploader.py`

Add the following function to list all folders with item counts:

```python
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
```

## 3. CLI Updates

Update the `cli.py` file to include the new command-line arguments:

1. Add new imports:
```python
from .uploader import (
    upload_files, 
    list_s3_folder_objects, 
    check_folder_exists, 
    download_folder,  # New import
    list_folders      # New import
)
```

2. Add new command-line arguments:
```python
parser.add_argument("-d", "--download", metavar="FOLDER", help="Download all files from a folder in the bucket")
parser.add_argument("-o", "--output", metavar="DIR", help="Output directory for downloads (used with -d)")
parser.add_argument("-ls", "--list", action="store_true", help="List all folders in the bucket with item count")
```

3. Add handlers for the new flags:
```python
# If list flag is provided, list all folders and exit
if args.list:
    print("Listing all folders in the bucket...")
    folders = asyncio.run(list_folders())
    if folders:
        print("\nFolders in S3 bucket:")
        print("-" * 50)
        print(f"{'Folder Name':<40} {'Items':<10}")
        print("-" * 50)
        for folder, count in sorted(folders):
            print(f"{folder:<40} {count:<10}")
        print("-" * 50)
        print(f"Total: {len(folders)} folders")
    else:
        print("No folders found or error listing folders.")
    return

# If download flag is provided, download the folder and exit
if args.download:
    folder = args.download
    output_dir = args.output if args.output else folder
    print(f"Downloading folder '{folder}' to '{output_dir}'...")
    asyncio.run(download_folder(folder, output_dir))
    return
```

## Usage Examples

### Listing Folders

```bash
# List all folders in the bucket with item counts
s3u -ls
```

Example output:
```
Listing all folders in the bucket...

Folders in S3 bucket:
--------------------------------------------------
Folder Name                              Items     
--------------------------------------------------
landscapes                               42        
portraits                                18        
watercolors                              37        
--------------------------------------------------
Total: 3 folders
```

### Downloading a Folder

```bash
# Download a folder using the default output directory
s3u -d watercolors

# Download a folder to a specific output directory
s3u -d watercolors -o ./downloaded_art
```

Example output:
```
Downloading folder 'watercolors' to 'watercolors'...
Found 37 files to download from watercolors
Downloaded: watercolors/image001.jpg -> watercolors/image001.jpg
Downloaded: watercolors/image002.jpg -> watercolors/image002.jpg
...
Downloaded 37 of 37 files to watercolors
```

## Implementation Steps

1. Add the new functions (`download_folder` and `list_folders`) to `uploader.py`
2. Update the import section in `cli.py` to include the new functions
3. Add the new command-line arguments to the argument parser
4. Add the handlers for the new flags in the `main()` function
5. Update the README.md to document the new features

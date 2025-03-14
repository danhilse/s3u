# S3 Upload Utility - Folder Existence Handling

This implementation adds the ability to check if a folder already exists in S3 and provides options for handling links from existing folders.

## Implementation Changes

### 1. Add Folder Existence Check Function to `uploader.py`

Add the following function to check if a folder already exists in S3:

```python
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
```

### 2. Modify the `list_s3_folder_objects` Function

Update this function to support returning only URLs without printing or clipboard operations:

```python
async def list_s3_folder_objects(s3_folder, return_urls_only=False):
    """
    List all objects in an S3 folder and return their CloudFront URLs.
    
    Args:
        s3_folder (str): The folder name in the S3 bucket to list
        return_urls_only (bool): If True, just return the URLs without printing or clipboard copy
    
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
```

### 3. Update the `upload_files` Function

Add a new parameter `include_existing` to control whether to include existing files:

```python
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
    # [existing code...]
    
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
```

### 4. Update the CLI in `cli.py`

Add code to check if the folder exists and ask the user how to handle existing files:

```python
# Get S3 folder
folder = get_input("S3 folder name", current_dir)

# Check if folder exists in S3
folder_exists = asyncio.run(check_folder_exists(folder))

# Initialize include_existing with default value
include_existing = True

if folder_exists:
    print(f"\nFolder '{folder}' already exists in S3 bucket.")
    include_existing_input = get_input("Include existing files in CDN links? (y/n)", "y")
    include_existing = include_existing_input.lower() == 'y'

# [rest of the code...]

# Update the upload_files call to include the new parameter
asyncio.run(upload_files(
    s3_folder=folder,
    extensions=extensions,
    rename_prefix=rename_prefix,
    only_first=only_first,
    max_concurrent=concurrent,
    source_dir=source_dir,
    specific_files=optimized_files,
    include_existing=include_existing  # Add this parameter
))
```

## Flow Diagram

```
Start
  |
  v
Get folder name from user
  |
  v
Check if folder exists in S3 bucket
  |
  v
If folder exists:
  |
  |---> Ask if user wants to include existing files
  |       |
  |       v
  |     User chooses "Yes" (default) or "No"
  |
  v
Upload new files to S3
  |
  v
If user chose to include existing files:
  |
  |---> Get list of existing files
  |       |
  |       v
  |     Combine with newly uploaded files
  |
  v
Copy URLs to clipboard (JSON array or single URL)
  |
  v
End
```

## Testing

1. Test with a new folder name that doesn't exist yet
2. Test with an existing folder name and choose to include existing files
3. Test with an existing folder name and choose NOT to include existing files
4. Test with the browse functionality to ensure it still works correctly

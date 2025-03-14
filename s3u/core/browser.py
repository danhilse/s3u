"""
Folder and file browsing functionality.
"""

import os
import sys
import pyperclip
from datetime import datetime
from botocore.exceptions import NoCredentialsError

from .s3_core import get_s3_session, get_bucket_name, get_cloudfront_url
from .formatter import format_output

async def list_folders(prefix=""):
    """
    List all folders in the S3 bucket with item count.
    
    Args:
        prefix (str): Optional prefix to filter folders
        
    Returns:
        list: List of tuples containing (folder_name, item_count)
    """
    session = get_s3_session()
    folders = {}
    
    try:
        async with session.client('s3') as s3:
            paginator = s3.get_paginator('list_objects_v2')
            
            async for page in paginator.paginate(Bucket=get_bucket_name(), Delimiter='/'):
                if 'CommonPrefixes' in page:
                    for prefix_obj in page['CommonPrefixes']:
                        folder_name = prefix_obj['Prefix'].rstrip('/')
                        folders[folder_name] = 0
            
            # Now count items in each folder
            for folder_name in folders.keys():
                folder_prefix = folder_name + '/'
                
                item_count = 0
                async for page in paginator.paginate(Bucket=get_bucket_name(), Prefix=folder_prefix):
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

async def list_s3_folder_objects(s3_folder, return_urls_only=False, limit=None, output_format='array', recursive=False):
    """
    List objects in an S3 folder and return their CloudFront URLs.
    
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
            
            if not return_urls_only:
                if not urls:
                    print(f"No objects found in folder: {s3_folder}" + (" (including subfolders)" if recursive else ""))
                else:
                    print(f"Found {len(urls)} objects in folder: {s3_folder}" + (" (including subfolders)" if recursive else ""))
                    
                    # Format the output based on the specified format
                    clipboard_content = format_output(urls, objects, output_format)
                    
                    # Copy to clipboard
                    pyperclip.copy(clipboard_content)
                    print(f"\nCopied {output_format} of {len(urls)} URLs to clipboard")
                
            return urls if output_format == 'array' or return_urls_only else objects
    except NoCredentialsError:
        print("Credentials not available")
        sys.exit(1)
    except Exception as e:
        print(f"Error listing objects in folder {s3_folder}: {str(e)}")
        return []
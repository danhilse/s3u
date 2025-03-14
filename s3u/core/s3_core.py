"""
Core S3 operations for the s3u utility.
"""

import os
import sys
import aioboto3
from botocore.exceptions import NoCredentialsError

# Import config functions
from ..config import load_config

def get_s3_session():
    """
    Create and return an aioboto3 session with profile from config.
    
    Returns:
        aioboto3.Session: A boto3 session for S3 operations
    """
    config = load_config()
    profile_name = config.get("aws_profile", "")
    return aioboto3.Session(profile_name=profile_name if profile_name else None)

def get_bucket_name():
    """
    Get the configured bucket name.
    
    Returns:
        str: The S3 bucket name from config
    """
    config = load_config()
    return config.get("bucket_name", "")

def get_cloudfront_url(s3_path=None):
    """
    Get CloudFront URL, optionally for a specific S3 path.
    
    Args:
        s3_path (str, optional): The S3 object path
        
    Returns:
        str: The CloudFront URL, with path if provided
    """
    config = load_config()
    base_url = config.get("cloudfront_url", "")
    
    if s3_path:
        return f"{base_url}/{s3_path}"
    else:
        return base_url

async def check_folder_exists(s3_folder):
    """
    Check if a folder already exists in the S3 bucket.
    
    Args:
        s3_folder (str): The folder name to check
        
    Returns:
        bool: True if the folder exists, False otherwise
    """
    session = get_s3_session()
    bucket_name = get_bucket_name()
    
    try:
        async with session.client('s3') as s3:
            # Add trailing slash if not present to ensure we're checking a folder
            folder_prefix = s3_folder if s3_folder.endswith('/') else f"{s3_folder}/"
            
            response = await s3.list_objects_v2(
                Bucket=bucket_name,
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
    """
    Ensure that an S3 folder exists by creating it if necessary.
    
    Args:
        session (aioboto3.Session): The boto3 session
        s3_folder (str): The folder name in the S3 bucket
        
    Returns:
        bool: True if successful, False otherwise
    """
    bucket_name = get_bucket_name()
    
    async with session.client('s3') as s3:
        try:
            await s3.put_object(Bucket=bucket_name, Key=(s3_folder + '/'))
            print(f"Ensured S3 folder exists: s3://{bucket_name}/{s3_folder}/")
            return True
        except NoCredentialsError:
            print("Credentials not available")
            sys.exit(1)
        except Exception as e:
            print(f"Error ensuring folder exists: {str(e)}")
            return False

def format_s3_path(s3_folder, filename):
    """
    Format an S3 path for an object.
    
    Args:
        s3_folder (str): The folder name in the S3 bucket
        filename (str): The filename
        
    Returns:
        str: The formatted S3 path
    """
    return f"{s3_folder}/{filename}" if s3_folder else filename
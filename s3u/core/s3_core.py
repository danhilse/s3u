"""
Core S3 operations for the s3u utility.
"""

import os
import sys
import aioboto3
from botocore.exceptions import NoCredentialsError

# Constants to be used across the application
BUCKET_NAME = "dh.images"
CLOUDFRONT_URL = "https://d1lbnboj0lfh6w.cloudfront.net"

def get_s3_session():
    """
    Create and return an aioboto3 session.
    
    Returns:
        aioboto3.Session: A boto3 session for S3 operations
    """
    return aioboto3.Session()

async def check_folder_exists(s3_folder):
    """
    Check if a folder already exists in the S3 bucket.
    
    Args:
        s3_folder (str): The folder name to check
        
    Returns:
        bool: True if the folder exists, False otherwise
    """
    session = get_s3_session()
    
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
    """
    Ensure that an S3 folder exists by creating it if necessary.
    
    Args:
        session (aioboto3.Session): The boto3 session
        s3_folder (str): The folder name in the S3 bucket
        
    Returns:
        bool: True if successful, False otherwise
    """
    async with session.client('s3') as s3:
        try:
            await s3.put_object(Bucket=BUCKET_NAME, Key=(s3_folder + '/'))
            print(f"Ensured S3 folder exists: s3://{BUCKET_NAME}/{s3_folder}/")
            return True
        except NoCredentialsError:
            print("Credentials not available")
            sys.exit(1)
        except Exception as e:
            print(f"Error ensuring folder exists: {str(e)}")
            return False

def get_cloudfront_url(s3_path):
    """
    Generate a CloudFront URL for an S3 object path.
    
    Args:
        s3_path (str): The S3 object path
        
    Returns:
        str: The CloudFront URL
    """
    return f"{CLOUDFRONT_URL}/{s3_path}"

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
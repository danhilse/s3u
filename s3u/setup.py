import os
import json
import boto3
import aioboto3
import asyncio

from .config import load_config, save_config, CONFIG_DIR
from .permissions import verify_permissions

async def run_setup():
    """Interactive setup wizard for first-time users."""
    print("\n=== S3 Upload Utility Setup ===\n")
    
    config = load_config()
    
    # Check if setup has already run
    if config.get("setup_complete", False):
        print("Configuration already exists. Run 's3u -config' to modify settings.")
        return
    
    print("This wizard will help you configure S3U for your AWS environment.")
    print("You'll need AWS credentials and an S3 bucket with CloudFront.\n")
    
    # Check for AWS credentials
    found_credentials = False
    available_profiles = []
    
    try:
        # Check for credentials file
        cred_file = os.path.expanduser("~/.aws/credentials")
        if os.path.exists(cred_file):
            print("✓ AWS credentials file found.")
            session = boto3.Session()
            available_profiles = session.available_profiles
            if available_profiles:
                print(f"Available profiles: {', '.join(available_profiles)}")
                found_credentials = True
        
        # Check for environment variables
        if "AWS_ACCESS_KEY_ID" in os.environ and "AWS_SECRET_ACCESS_KEY" in os.environ:
            print("✓ AWS credentials found in environment variables.")
            found_credentials = True
    except Exception as e:
        print(f"Error checking credentials: {str(e)}")
    
    if not found_credentials:
        print("\n⚠️ No AWS credentials found. Please set up AWS CLI credentials:")
        print("   Run 'aws configure' or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
        print("   Then restart this setup.\n")
        return
    
    # Get AWS profile
    if available_profiles:
        default_profile = available_profiles[0] if available_profiles else ""
        profile = input(f"AWS profile to use [default: {default_profile}]: ").strip() or default_profile
        config["aws_profile"] = profile
    
    # Create aioboto3 session for permission checks
    session = aioboto3.Session(profile_name=config["aws_profile"] or None)
    
    # Get S3 bucket information
    bucket_name = input("S3 bucket name: ").strip()
    while not bucket_name:
        print("Bucket name is required.")
        bucket_name = input("S3 bucket name: ").strip()
    
    config["bucket_name"] = bucket_name
    
    # Get CloudFront URL
    cloudfront_url = input("CloudFront distribution URL (https://xxxx.cloudfront.net): ").strip()
    config["cloudfront_url"] = cloudfront_url
    
    print("\nVerifying AWS permissions...")
    permissions = await verify_permissions(session, bucket_name, cloudfront_url)
    
    # Display permission status
    print("\nPermission check results:")
    print(f"  {'✓' if permissions['s3_list'] else '✗'} List bucket contents")
    print(f"  {'✓' if permissions['s3_read'] else '✗'} Read objects from bucket")
    print(f"  {'✓' if permissions['s3_write'] else '✗'} Write objects to bucket")
    if cloudfront_url:
        print(f"  {'✓' if permissions['cloudfront_access'] else '✗'} CloudFront URL format")
    
    if not all([permissions['s3_list'], permissions['s3_read'], permissions['s3_write']]):
        print("\n⚠️ Some permissions are missing. You may need to update your IAM policy.")
        print_iam_policy_template(bucket_name)
    
    # Set setup as complete and save config
    config["setup_complete"] = True
    save_config(config)
    
    print("\n✓ Setup complete! You can now use S3U.")
    print(f"Configuration saved to {os.path.join(CONFIG_DIR, 'config.json')}")
    print("Run 's3u -config' at any time to update your settings.")

def print_iam_policy_template(bucket_name):
    """Print a template IAM policy for the given bucket."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}/*"
                ]
            }
        ]
    }
    
    print("\nRequired IAM policy:")
    print(json.dumps(policy, indent=2))
    print("\nYou can attach this policy to your IAM user or role.")
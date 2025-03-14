import os
import json
import boto3
import aioboto3
import asyncio
import readline

from .config import load_config, save_config, CONFIG_DIR
from .permissions import verify_permissions
from .utils import find_cloudfront_for_bucket

async def list_available_buckets(session):
    """List available S3 buckets in the AWS account."""
    try:
        # Use standard boto3 for bucket listing since it's simpler
        if isinstance(session, aioboto3.Session):
            # Convert aioboto3 session to boto3 session for synchronous operation
            boto3_session = boto3.Session(
                profile_name=session._profile_name
            )
            s3_client = boto3_session.client('s3')
        else:
            s3_client = session.client('s3')
            
        response = s3_client.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        return buckets
    except Exception as e:
        print(f"Error listing buckets: {str(e)}")
        print("This is normal if your IAM user doesn't have 's3:ListAllMyBuckets' permission.")
        return []

def setup_completion(options):
    """Set up tab completion for the provided options."""
    import readline
    
    def complete(text, state):
        matches = [opt for opt in options if opt.startswith(text)]
        return matches[state] if state < len(matches) else None
    
    readline.set_completer(complete)
    readline.set_completer_delims(' \t\n')
    readline.parse_and_bind('tab: complete')

def get_input_with_completion(prompt, options=None, default=None):
    """Get user input with tab completion for the provided options."""
    if options:
        setup_completion(options)
    
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    value = input(full_prompt).strip()
    
    # Reset completion
    readline.set_completer(None)
    
    return value if value else default

async def run_setup(force=False):
    """
    Interactive setup wizard for first-time users.
    
    Args:
        force (bool): If True, run setup even if already configured
    """
    print("\n=== S3 Upload Utility Setup ===\n")
    
    config = load_config()
    
    # Check if setup has already run
    if config.get("setup_complete", False) and not force:
        print("Configuration already exists. Use 's3u -setup' to run the setup wizard again.")
        print("Or run 's3u -config' to modify specific settings.")
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
    selected_profile = None
    if available_profiles:
        default_profile = available_profiles[0] if available_profiles else ""
        selected_profile = get_input_with_completion(
            "AWS profile to use",
            options=available_profiles,
            default=default_profile
        )
        config["aws_profile"] = selected_profile
    
    # Create aioboto3 session for permission checks
    session = aioboto3.Session(profile_name=config.get("aws_profile") or None)
    
    # Create boto3 session for listing buckets
    boto3_session = boto3.Session(profile_name=config.get("aws_profile") or None)
    
    # List available buckets
    print("\nAttempting to fetch available S3 buckets...")
    available_buckets = await list_available_buckets(boto3_session)
    
    if available_buckets:
        print(f"Found {len(available_buckets)} buckets in your AWS account:")
        for i, bucket in enumerate(available_buckets[:10], 1):  # Show first 10 buckets
            print(f"  {i}. {bucket}")
        if len(available_buckets) > 10:
            print(f"  ... and {len(available_buckets) - 10} more")
        
        # Select default bucket (first one)
        default_bucket = available_buckets[0] if available_buckets else ""
        
        # Get bucket with tab completion (but don't mention it in the prompt)
        bucket_name = get_input_with_completion(
            "S3 bucket name",
            options=available_buckets,
            default=default_bucket
        )
    else:
        print("\nUnable to list buckets. This is likely due to missing permissions.")
        print("To get a list of your buckets, you need the 's3:ListAllMyBuckets' permission.")
        print("\nYou can add the following policy to your IAM user:")
        print(json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:ListAllMyBuckets"],
                    "Resource": "*"
                }
            ]
        }, indent=2))
        print("\nAlternatively, you can continue setup by entering your bucket name manually:")
        bucket_name = input("S3 bucket name: ").strip()
    
    while not bucket_name:
        print("Bucket name is required.")
        bucket_name = input("S3 bucket name: ").strip()
    
    config["bucket_name"] = bucket_name
    
    # Try to find associated CloudFront distributions
    print("\nLooking for CloudFront distributions associated with this bucket...")
    
    cloudfront_distributions = await find_cloudfront_for_bucket(boto3_session, bucket_name)
    
    if cloudfront_distributions:
        print(f"Found {len(cloudfront_distributions)} CloudFront distribution(s) for this bucket:")
        for i, (dist_id, domain) in enumerate(cloudfront_distributions, 1):
            print(f"  {i}. https://{domain} (ID: {dist_id})")
        
        # Always provide a default (first distribution)
        default_cloudfront = f"https://{cloudfront_distributions[0][1]}"
        
        # Build options list for completion
        cloudfront_options = [f"https://{domain}" for _, domain in cloudfront_distributions]
        
        cloudfront_url = get_input_with_completion(
            "CloudFront distribution URL",
            options=cloudfront_options,
            default=default_cloudfront
        )
    else:
        print("No CloudFront distributions found for this bucket.")
        print("You may need the 'cloudfront:ListDistributions' permission to auto-detect distributions.")
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
    print("\nTo use S3U, run the command again without the -setup flag.")

def print_iam_policy_template(bucket_name):
    """Print a template IAM policy for the given bucket."""
    # Complete recommended policy for s3u (includes bucket listing and CloudFront)
    complete_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListAllMyBuckets"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:GetBucketLocation"
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
            },
            {
                "Effect": "Allow",
                "Action": [
                    "cloudfront:ListDistributions"
                ],
                "Resource": "*"
            }
        ]
    }
    
    print("\nRecommended IAM policy for s3u:")
    print(json.dumps(complete_policy, indent=2))
    
    print("\nThis policy includes:")
    print("  - Listing all buckets (for easier setup)")
    print(f"  - Listing contents of the '{bucket_name}' bucket")
    print(f"  - Reading, uploading, and deleting objects in the '{bucket_name}' bucket")
    print("  - Listing CloudFront distributions (for auto-detection)")
    print("\nYou can attach this policy to your IAM user or role.")
"""
AWS Helper utilities for S3U
"""

async def find_cloudfront_for_bucket(session, bucket_name):
    """
    Find CloudFront distributions associated with the given S3 bucket.
    
    Args:
        session: boto3/aioboto3 session
        bucket_name: Name of the S3 bucket
        
    Returns:
        List of tuples (distribution_id, domain_name) for matching distributions
    """
    try:
        if hasattr(session, 'client'):
            # Standard boto3 session
            cloudfront = session.client('cloudfront')
            response = cloudfront.list_distributions()
        else:
            # Async aioboto3 session
            async with session.client('cloudfront') as cloudfront:
                response = await cloudfront.list_distributions()
        
        # Extract distribution list or handle empty case
        if 'DistributionList' not in response or 'Items' not in response['DistributionList']:
            return []
            
        distributions = response['DistributionList']['Items']
        matching_distributions = []
        
        # Track already added distributions to avoid duplicates
        added_distribution_ids = set()
        
        # Handle various bucket origin patterns
        bucket_origin_patterns = [
            f"{bucket_name}.s3.",                     # Standard bucket URL pattern
            f"{bucket_name}.s3.amazonaws.com",        # Classic endpoint
            f"{bucket_name}.s3-website.",             # Website endpoint
            f"{bucket_name}.s3-{session.region_name}" # Regional endpoint
        ]
        
        print(f"Searching for CloudFront distributions for bucket: {bucket_name}")
        
        for dist in distributions:
            # Skip if we've already added this distribution
            if dist['Id'] in added_distribution_ids:
                continue
                
            # Check if this distribution has the bucket as an origin
            if 'Origins' not in dist or 'Items' not in dist['Origins']:
                continue
                
            for origin in dist['Origins']['Items']:
                origin_domain = origin.get('DomainName', '')
                match_found = False
                
                # Check all possible origin patterns
                for pattern in bucket_origin_patterns:
                    if pattern in origin_domain:
                        match_found = True
                        break
                
                # Also check for custom origins with bucket name
                if not match_found and bucket_name in origin_domain:
                    match_found = True
                
                if match_found and dist['Id'] not in added_distribution_ids:
                    matching_distributions.append((
                        dist['Id'],
                        dist['DomainName']
                    ))
                    added_distribution_ids.add(dist['Id'])
                    print(f"  ✓ Found: {dist['DomainName']} (ID: {dist['Id']}) - {origin_domain}")
                    break
        
        return matching_distributions
        
    except Exception as e:
        print(f"Error finding CloudFront distributions: {str(e)}")
        print("This is normal if you don't have cloudfront:ListDistributions permission.")
        return []
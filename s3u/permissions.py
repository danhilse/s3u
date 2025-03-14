async def verify_permissions(session, bucket_name, cloudfront_url=None):
    """Verify AWS permissions for S3U operations."""
    results = {
        "s3_list": False,
        "s3_read": False,
        "s3_write": False,
        "cloudfront_access": False,
    }
    
    try:
        # Test S3 listing
        async with session.client('s3') as s3:
            await s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            results["s3_list"] = True
            
            # Test S3 write
            test_key = ".s3u_permission_test"
            try:
                await s3.put_object(Bucket=bucket_name, Key=test_key, Body="test")
                results["s3_write"] = True
                
                # Test S3 read
                await s3.get_object(Bucket=bucket_name, Key=test_key)
                results["s3_read"] = True
                
                # Clean up
                await s3.delete_object(Bucket=bucket_name, Key=test_key)
            except Exception as e:
                print(f"Write/read test failed: {str(e)}")
        
        # Test CloudFront if URL provided
        if cloudfront_url:
            # Simple check to ensure CloudFront URL format is valid
            if cloudfront_url.startswith("https://") and ".cloudfront.net" in cloudfront_url:
                results["cloudfront_access"] = True
    
    except Exception as e:
        print(f"Permission verification failed: {str(e)}")
    
    return results
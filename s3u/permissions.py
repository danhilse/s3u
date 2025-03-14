async def verify_permissions(session, bucket_name, cloudfront_url=None):
    """Verify AWS permissions for S3U operations."""
    results = {
        "s3_list": False,
        "s3_read": False,
        "s3_write": False,
        "cloudfront_access": False,
        "bucket_exists": False
    }
    
    try:
        # Test S3 listing
        async with session.client('s3') as s3:
            # First, check if the bucket exists by trying to list its contents
            try:
                await s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
                results["s3_list"] = True
                results["bucket_exists"] = True
                print(f"✓ Successfully connected to bucket '{bucket_name}'")
            except Exception as e:
                error_message = str(e)
                if "NoSuchBucket" in error_message:
                    print(f"✗ Bucket '{bucket_name}' does not exist")
                    return results
                elif "AccessDenied" in error_message:
                    print(f"✗ Access denied when listing objects in '{bucket_name}'")
                    print("  This may be fine if your permissions are limited to specific paths")
                else:
                    print(f"✗ Error accessing bucket: {error_message}")
            
            # Test S3 write
            test_key = ".s3u_permission_test"
            try:
                await s3.put_object(Bucket=bucket_name, Key=test_key, Body="test")
                results["s3_write"] = True
                print(f"✓ Write test successful")
                
                # Test S3 read
                try:
                    await s3.get_object(Bucket=bucket_name, Key=test_key)
                    results["s3_read"] = True
                    print(f"✓ Read test successful")
                except Exception as e:
                    print(f"✗ Read test failed: {str(e)}")
                
                # Clean up
                try:
                    await s3.delete_object(Bucket=bucket_name, Key=test_key)
                    print(f"✓ Test file deleted successfully")
                except Exception as e:
                    print(f"! Warning: Could not delete test file: {str(e)}")
            except Exception as e:
                print(f"✗ Write test failed: {str(e)}")
        
        # Test CloudFront if URL provided
        if cloudfront_url:
            # Simple check to ensure CloudFront URL format is valid
            if cloudfront_url.startswith("https://") and ".cloudfront.net" in cloudfront_url:
                results["cloudfront_access"] = True
                print(f"✓ CloudFront URL format appears valid")
            else:
                print(f"✗ CloudFront URL format is invalid. Should be like 'https://xxxx.cloudfront.net'")
    
    except Exception as e:
        print(f"✗ Permission verification failed: {str(e)}")
    
    return results
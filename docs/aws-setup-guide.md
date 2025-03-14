# AWS Setup Guide for S3U

This guide walks you through setting up the required AWS resources for the S3 Upload Utility.

## 1. AWS Credentials

First, you need AWS credentials configured on your system:

### Option 1: AWS CLI (Recommended)

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
```

### Option 2: Environment Variables

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-1"
```

## 2. Create an S3 Bucket

1. Go to the [S3 console](https://console.aws.amazon.com/s3/)
2. Click "Create bucket"
3. Enter a globally unique bucket name
4. Choose a region close to your users
5. Configure options:
   - Enable versioning (recommended)
   - Apply default encryption (recommended)
6. Configure permissions:
   - Uncheck "Block all public access" if you need direct S3 URLs
   - Add bucket policy (see below for CloudFront setup)
7. Create the bucket

## 3. Set Up CloudFront

1. Go to the [CloudFront console](https://console.aws.amazon.com/cloudfront/)
2. Click "Create Distribution"
3. For Origin Domain, select your S3 bucket
4. Configure settings:
   - Origin access: "Origin access control settings (recommended)"
   - Create a new OAC
   - Origin access control: "Create control setting"
   - Sign requests: Yes
   - Add the bucket policy that CloudFront provides
5. Default cache behavior:
   - Viewer protocol policy: "Redirect HTTP to HTTPS"
   - Cache policy: "CachingOptimized"
6. Create the distribution

After creating the distribution, note the domain name (e.g., `d1234abcd.cloudfront.net`). You'll need this during S3U setup.

## 4. Configure IAM Permissions

Create an IAM policy with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET-NAME"
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
        "arn:aws:s3:::YOUR-BUCKET-NAME/*"
      ]
    }
  ]
}
```

Attach this policy to your IAM user or role.

## 5. Test Your Setup

After configuring S3U, verify your setup:

```bash
# Check permissions
s3u --check-permissions

# List buckets
s3u -ls

# Upload a test file
s3u -t test.jpg
```

## 6. Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| "Access Denied" errors | Check IAM permissions and bucket policy |
| "No credentials found" | Run `aws configure` or set environment variables |
| CloudFront showing 403 errors | Verify OAC settings and bucket policy |
| Files not appearing in CloudFront | Wait for distribution to deploy (~5-30 minutes) |

### Checking your CloudFront Origin Access Control

To verify your CloudFront OAC is correctly set up:

1. In CloudFront console, select your distribution
2. Go to the "Origins" tab
3. Check that the origin has "Origin access control settings" selected
4. Verify the bucket policy includes the CloudFront service principal

### Verifying S3 Bucket Policy

Your bucket policy should look similar to this when using OAC:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipal",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::ACCOUNT-ID:distribution/DISTRIBUTION-ID"
        }
      }
    }
  ]
}
```

## 7. Additional Resources

- [AWS S3 Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)
- [AWS CloudFront Documentation](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html)
- [AWS IAM Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html)

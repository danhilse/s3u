# S3U User Guide

## Table of Contents
- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [First-Time Setup](#first-time-setup)
- [Basic Usage](#basic-usage)
  - [Interactive Mode](#interactive-mode)
  - [Command Line Options](#command-line-options)
  - [Quick Mode](#quick-mode)
- [Working with Files](#working-with-files)
  - [File Extensions](#file-extensions)
  - [Image Optimization](#image-optimization)
  - [Video Support](#video-support)
  - [File Renaming](#file-renaming)
- [Working with Folders](#working-with-folders)
  - [Tab Completion](#tab-completion)
  - [Existing Folders](#existing-folders)
  - [Subfolder Handling](#subfolder-handling)
  - [Listing Folders](#listing-folders)
- [Downloading Content](#downloading-content)
  - [Basic Downloads](#basic-downloads)
  - [Advanced Download Options](#advanced-download-options)
- [Configuration System](#configuration-system)
  - [Configuration File](#configuration-file)
  - [Configuration Commands](#configuration-commands)
  - [Output Formats](#output-formats)
- [CloudFront Integration](#cloudfront-integration)
  - [URL Generation](#url-generation)
  - [Browsing CDN Links](#browsing-cdn-links)
- [AWS Setup](#aws-setup)
  - [Required Permissions](#required-permissions)
  - [Bucket Configuration](#bucket-configuration)
- [Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)
  - [Debugging Tips](#debugging-tips)
- [Advanced Topics](#advanced-topics)
  - [Concurrent Uploads](#concurrent-uploads)
  - [Custom AWS Profiles](#custom-aws-profiles)

## Introduction

S3U (S3 Upload Utility) is an interactive command-line tool designed to simplify and enhance the process of uploading files to Amazon S3 with CloudFront integration. It offers a range of features including image optimization, batch uploading, file renaming, and much more.

Key benefits of using S3U:

- **Streamlined workflows** - Interactive interface eliminates the need to remember complex AWS CLI commands
- **Time savings** - Concurrent uploads and batch processing speed up your workflow
- **Image optimization** - Built-in image processing using FFmpeg reduces file sizes
- **Flexibility** - Supports various file types, renaming options, and subfolder handling

Whether you're managing a content repository, uploading assets for a website, or organizing a media library, S3U simplifies the process of getting your files into the cloud and generating accessible URLs.

## Getting Started

### Prerequisites

Before using S3U, ensure you have:

1. **Python 3.7+** installed on your system
2. **FFmpeg and FFprobe** installed (required for image optimization)
3. **AWS credentials** configured in your environment
4. An **S3 bucket** with appropriate permissions
5. A **CloudFront distribution** connected to your S3 bucket (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/s3u.git
cd s3u

# Install the package
pip install -e .
```

This installs S3U in development mode, allowing you to easily update it by pulling changes from the repository.

### First-Time Setup

The first time you run S3U, it will guide you through setting up your AWS configuration:

```bash
s3u
```

During setup, you'll need to provide:

1. Your **AWS profile** (if you have multiple profiles configured)
2. Your **S3 bucket name**
3. Your **CloudFront distribution URL**

S3U will verify your AWS permissions and store these settings in a configuration file for future use.

If you need to re-run the setup process:

```bash
s3u -setup
```

## Basic Usage

### Interactive Mode

The default mode is interactive, guiding you through each step of the upload process:

```bash
s3u
```

You'll be prompted for:

1. Which file types to include
2. Whether to optimize images
3. The destination S3 folder
4. File renaming options
5. Subfolder handling
6. Output format preferences

Each prompt includes a default value in brackets that you can accept by pressing Enter.

### Command Line Options

For common tasks, S3U provides command-line options to bypass the interactive prompts:

```bash
# Upload with 15 concurrent connections
s3u -c 15

# Get all CDN links from an existing folder
s3u -b mj_watercolors

# List all folders in the bucket
s3u -ls

# Download files from a folder
s3u -d mj_watercolors
```

See the [Command Line Options](#command-line-options) section in the README for a full list of available options.

### Quick Mode

When you need to upload files with minimal interaction, use quick mode:

```bash
s3u -q
```

In quick mode, S3U uses default settings and uploads to a folder named "default". This is ideal for rapid uploads when you don't need custom settings.

## Working with Files

### File Extensions

S3U allows you to filter which files to include based on their extensions:

```
Extensions: jpg png mp4
```

You can:
- Specify multiple extensions separated by spaces or commas
- Use predefined groups: `images`, `videos`, or `documents`
- Enter `all` or leave blank to include all files

Predefined extension groups:
- **images**: jpg, jpeg, png, gif, webp, svg
- **videos**: mp4, mov, avi, webm, mkv
- **documents**: pdf, doc, docx, txt, md

### Image Optimization

S3U can optimize images before uploading to reduce file sizes and improve loading times:

```
Optimize media before uploading? (y/n) [n]: y
```

If you choose to optimize images, you can select from three size options:

1. **optimized** (1920px) - High quality, suitable for full-screen viewing
2. **small** (1080px) - Medium quality, good for web pages
3. **tiny** (640px) - Small size, ideal for thumbnails
4. **patches** (1280px) - Special mode with higher compression

You can also select the output format:
- **WebP** - Best balance of quality and file size
- **JPEG** - Maximum compatibility
- **AVIF** - Best compression but limited browser support

### Video Support

S3U supports video files (MP4, MOV) and can optionally transcode them:

```
Optimize videos as well? (y/n) [n]: y
```

Video optimization options include:
- **Format**: MP4 (compatible) or WebM (better compression)
- **Encoding preset**: Fast, Medium, or Slow (smaller files but takes longer)
- **Audio removal**: Option to strip audio tracks (for pATCHES mode)

### File Renaming

You can rename files during upload with a common prefix:

```
Rename prefix (optional, press Enter to skip): vacation2023
```

S3U offers three renaming modes (configurable via `-config rename_mode`):

1. **replace** - Original filenames are replaced completely (e.g., `vacation_001.jpg`)
2. **prepend** - Prefix is added before the original filename (e.g., `vacation_beach.jpg`)
3. **append** - Prefix is added after the original filename (e.g., `beach_vacation.jpg`)

## Working with Folders

### Tab Completion

When entering an S3 folder name, S3U offers tab completion for existing folders:

```
S3 folder name: vaca[TAB]
```

Pressing Tab will display available folders matching what you've typed and allow you to cycle through options.

### Existing Folders

When uploading to a folder that already exists in S3, S3U asks how to handle existing files:

```
Folder 'vacation_photos' already exists in S3 bucket.
Include existing files in CDN links? (y/n) [y]: 
```

- Answer **y** (default) to include all files (existing + new) in the clipboard output
- Answer **n** to include only the newly uploaded files

### Subfolder Handling

S3U offers three ways to handle local subfolders during upload:

```
Detected 3 subfolders in the current directory:
  1. images/products
  2. images/banners
  3. backup
  ... and 2 more
  
How to handle subfolders? (1=ignore, 2=pool all files, 3=preserve structure) [1]: 
```

1. **ignore** (default) - Only upload files in the main directory
2. **pool** - Combine all files from subfolders into the main S3 folder
3. **preserve** - Maintain the subfolder structure in S3

You can also specify this via command line:

```bash
s3u -sf preserve
```

### Listing Folders

To see all folders in your S3 bucket with item counts:

```bash
s3u -ls
```

Example output:
```
Folders in S3 bucket:
--------------------------------------------------
Folder Name                              Items     
--------------------------------------------------
landscapes                               42        
portraits                                18        
watercolors                              37        
--------------------------------------------------
Total: 3 folders
```

## Downloading Content

### Basic Downloads

To download all files from a folder:

```bash
s3u -d mj_watercolors
```

This creates a local directory with the same name and downloads all files.

### Advanced Download Options

You can customize downloads with additional options:

```bash
# Download only 5 files from a folder
s3u -d mj_watercolors 5

# Download to a specific directory
s3u -d mj_watercolors -o ./downloaded_images

# Download files recursively including subfolders
s3u -d mj_watercolors -sf preserve
```

## Configuration System

### Configuration File

S3U stores settings in a JSON file at `~/.s3u/config.json`. You can edit this file directly or use the configuration commands.

Example configuration file:
```json
{
    "format": "json",
    "concurrent": 10,
    "optimize": "auto",
    "size": "optimized",
    "rename_mode": "replace",
    "subfolder_mode": "ignore"
}
```

### Configuration Commands

View and modify configuration settings with these commands:

```bash
# Show current configuration
s3u -config

# Configure a specific option interactively
s3u -config format

# Set a specific option directly
s3u -config format json
```

Available configuration options:

| Option | Description | Allowed Values | Default |
|--------|-------------|----------------|---------|
| format | Output format for generated URLs | array, json, xml, html, csv | array |
| concurrent | Default number of concurrent uploads | 1-20 | 5 |
| optimize | Default image optimization setting | auto, always, never | auto |
| size | Default optimization size | optimized, small, tiny | optimized |
| rename_mode | How to apply rename prefix to filenames | replace, prepend, append | replace |
| subfolder_mode | How to handle subfolders when uploading | ignore, pool, preserve | ignore |

### Output Formats

S3U supports multiple output formats for CloudFront URLs:

- **array**: Simple JSON array of URLs (default)
- **json**: JSON object with metadata including file size, type, and timestamps
- **xml**: XML document with file metadata
- **html**: HTML document with clickable links
- **csv**: CSV file format with URL and metadata columns

Example JSON output:
```json
{
  "folder": "vacation_photos",
  "count": 3,
  "timestamp": "2023-08-15T14:22:33.456789",
  "files": [
    {
      "url": "https://d1lbnboj0lfh6w.cloudfront.net/vacation_photos/beach.jpg",
      "filename": "beach.jpg",
      "s3_path": "vacation_photos/beach.jpg",
      "size": 245678,
      "last_modified": "2023-08-15T14:20:12.345678",
      "type": "jpg"
    },
    ...
  ]
}
```

## CloudFront Integration

### URL Generation

S3U automatically generates CloudFront URLs for all uploaded files. These URLs are copied to your clipboard in the format specified in your configuration.

Example CloudFront URL:
```
https://d1lbnboj0lfh6w.cloudfront.net/vacation_photos/beach.jpg
```

### Browsing CDN Links

To get CloudFront URLs for files in an existing folder:

```bash
s3u -b vacation_photos
```

This copies URLs for all files in the folder to your clipboard.

You can limit the number of URLs:

```bash
s3u -b vacation_photos 12
```

## AWS Setup

### Required Permissions

S3U requires these AWS permissions:

1. **S3 bucket access**:
   - `s3:ListBucket`
   - `s3:GetObject`
   - `s3:PutObject`
   - `s3:DeleteObject`

2. **CloudFront access** (for auto-detection):
   - `cloudfront:ListDistributions`

Sample IAM policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name"
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
        "arn:aws:s3:::your-bucket-name/*"
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
```

### Bucket Configuration

Your S3 bucket should be configured to work with CloudFront:

1. Set up a CloudFront distribution with your S3 bucket as the origin
2. Configure Origin Access Control (OAC) for proper security
3. Update the bucket policy to allow CloudFront access

For detailed setup instructions, see the [AWS Setup Guide](docs/aws-setup-guide.md).

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| "No credentials found" | Run `aws configure` or set AWS environment variables |
| "Access denied" errors | Verify IAM permissions and bucket policy |
| Missing FFmpeg | Install FFmpeg and FFprobe for image optimization |
| Optimization not working | Check FFmpeg installation and file permissions |
| Tab completion not working | Ensure readline module is installed |
| CloudFront URLs not loading | Check CloudFront distribution is deployed and enabled |

### Debugging Tips

1. **Check AWS credentials**:
   ```bash
   aws s3 ls
   ```
   
2. **Verify FFmpeg installation**:
   ```bash
   ffmpeg -version
   ffprobe -version
   ```

3. **Test S3 bucket access**:
   ```bash
   aws s3 ls s3://your-bucket-name/
   ```

4. **Examine configuration file**:
   ```bash
   cat ~/.s3u/config.json
   ```

5. **Run S3U in verbose mode** (coming in future version):
   ```bash
   s3u -v
   ```

## Advanced Topics

### Concurrent Uploads

S3U can upload multiple files simultaneously to speed up the process:

```bash
s3u -c 15
```

This sets the maximum concurrent uploads to 15. The optimal value depends on your internet connection and the size of your files. For large files or slow connections, a lower value may be better.

You can set the default concurrency in your configuration:

```bash
s3u -config concurrent 10
```

### Custom AWS Profiles

If you have multiple AWS profiles configured, you can specify which one to use:

```bash
# During setup
s3u -setup

# Choose your profile when prompted
AWS profile to use [default]: production
```

This is particularly useful for managing uploads to different environments or AWS accounts.

---

## Additional Resources

- [AWS S3 Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)
- [AWS CloudFront Documentation](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

For more information and updates, visit the project repository: [https://github.com/yourusername/s3u](https://github.com/yourusername/s3u)
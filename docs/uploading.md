# S3U Core Uploading Guide

This guide provides a detailed explanation of S3U's core file uploading capabilities. The upload functionality is the heart of S3U, designed to efficiently transfer files to Amazon S3 and generate CloudFront URLs.

## Table of Contents

- [Uploading Workflow](#uploading-workflow)
- [Upload Modes](#upload-modes)
- [Concurrent Uploads](#concurrent-uploads)
- [Progress Tracking](#progress-tracking)
- [Subfolder Handling](#subfolder-handling)
- [Error Handling](#error-handling)
- [Post-Upload Actions](#post-upload-actions)
- [Advanced Upload Options](#advanced-upload-options)
- [Technical Implementation](#technical-implementation)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Uploading Workflow

The S3U upload process follows these steps:

1. **Initialization**: Verify AWS credentials and S3 bucket
2. **File Selection**: Identify files to upload based on extensions
3. **File Preparation**: Optionally rename files and/or optimize media
4. **Folder Preparation**: Create or verify the destination S3 folder
5. **Upload Execution**: Transfer files to S3 with concurrent uploads
6. **URL Generation**: Create CloudFront URLs for uploaded files
7. **Output**: Copy URLs to clipboard in the configured format

### Interactive Workflow Example

```
$ s3u

S3 Upload Utility
-----------------

File extensions to include:
  • Enter 'all' or leave blank for all files (default)
  • Enter specific types separated by spaces or commas (e.g., 'jpg png mp4')
  • Or use one of these groups:
    - images: jpg, jpeg, png, gif, webp, svg
    - videos: mp4, mov, avi, webm, mkv
    - documents: pdf, doc, docx, txt, md
Extensions [all]: images

Using images group: jpg, jpeg, png, gif, webp, svg
Optimize media before uploading? (y/n) [n]: y

Select size (1=optimized [1920px], 2=small [1080px], 3=tiny [640px], 4=pATCHES [1280px, high compression]) [1]: 2

Image format (1=webp [recommended], 2=jpg [compatible], 3=avif [best compression]) [1]: 1

Parallel optimization workers (1-16, higher=faster) [4]: 4

Enter folder name (press Tab to see existing folders)
S3 folder name [current_directory]: vacation_photos

Rename prefix (optional, press Enter to skip): beach_trip

Proceed with upload? (y/n) [y]: y

Upload Settings:
  Extensions: jpg, jpeg, png, gif, webp, svg
  Subfolder handling: ignore
  Media optimization: small
  Image format: webp
  Video optimization: Disabled
  Parallel workers: 4
  S3 Folder: vacation_photos
  Rename Prefix: beach_trip
  Rename Mode: replace (from config)
  Output Format: Array (from config)
  Concurrent Uploads: 5 (from config)

Starting media optimization...
Successfully optimized 15 files in ./optimized/small

Starting upload of 15 files...
Uploading beach_trip_001.webp: 100.0% | 3.45 MB/s | ETA: 0s
Uploading beach_trip_002.webp: 100.0% | 2.98 MB/s | ETA: 0s
[...]

Completed 15 of 15 uploads
Including existing files in the CDN links...
Total of 15 files in folder (new + existing)

Copied array format data to clipboard
```

## Upload Modes

S3U supports different modes for uploading files:

### Interactive Mode (Default)

The standard mode that guides you through the process with prompts:

```bash
s3u
```

### Quick Mode

Uploads files with default settings for a streamlined experience:

```bash
s3u -q
```

In quick mode:
- All files in the current directory are uploaded
- Files are uploaded to a folder named "default"
- Default configuration settings are used
- No optimization, renaming, or special handling is applied

### Command Line Mode

Specify options directly via command line arguments:

```bash
s3u -c 15 -sf preserve
```

This mode allows you to specify parameters without interactive prompts.

## Concurrent Uploads

S3U uses asynchronous programming to upload multiple files simultaneously, dramatically improving performance.

### How Concurrency Works

1. A semaphore controls the maximum number of simultaneous uploads
2. Each file upload runs as an independent task
3. The system automatically balances resources and network connections

### Setting Concurrency

You can set the concurrency level in several ways:

1. **Command-line flag** (for a single session):
   ```bash
   s3u -c 15
   ```

2. **Configuration** (persistent setting):
   ```bash
   s3u -config concurrent 10
   ```

3. **Interactive prompt** (if not using other methods)

### Optimal Concurrency Values

The ideal concurrency depends on your network and file sizes:

- **Large files** (videos, high-res images): 3-5 concurrent uploads
- **Medium files** (regular images, documents): 5-10 concurrent uploads
- **Small files** (tiny images, text files): 10-20 concurrent uploads
- **Slow connections**: Lower values (3-5) to avoid timeouts
- **Fast connections**: Higher values (10-15) for maximum throughput

## Progress Tracking

S3U provides detailed progress information during uploads.

### Per-File Progress

For each file being uploaded, S3U shows:

1. **Percentage complete**: How much of the file has been uploaded
2. **Upload speed**: Current transfer rate in B/s, KB/s, or MB/s
3. **ETA**: Estimated time remaining for the current file

Example:
```
Uploading beach_sunset.jpg: 78.5% | 2.45 MB/s | ETA: 12s
```

### Overall Progress

After all uploads complete, you'll see a summary:

```
Completed 15 of 15 uploads
Including existing files in the CDN links...
Total of 23 files in folder (new + existing)
```

This tells you:
1. How many files were successfully uploaded
2. The total number of files in the destination folder
3. Whether existing files were included in the results

## Subfolder Handling

S3U provides three ways to handle local subfolders during upload:

### Ignore Mode (Default)

Only uploads files from the current directory:

```bash
s3u -sf ignore
```

- Files in subfolders are skipped
- Simplest approach for flat file structures

### Pool Mode

Combines all files from all subfolders into a single S3 folder:

```bash
s3u -sf pool
```

- Files from all subfolders are "flattened" into the destination folder
- Useful for consolidating content from multiple directories
- Warning: May cause filename conflicts if different subfolders contain files with the same name

### Preserve Mode

Maintains your local folder structure in S3:

```bash
s3u -sf preserve
```

- Creates matching subfolder structure in S3
- Most organized approach for complex file hierarchies
- Ideal for websites and structured content

### Example Scenario

Consider this local directory structure:

```
project/
├── images/
│   ├── logo.png
│   └── banner.jpg
├── documents/
│   └── spec.pdf
└── README.md
```

With different subfolder modes:

- **Ignore mode**: Only `README.md` is uploaded
- **Pool mode**: All files are uploaded to the same S3 folder (`logo.png`, `banner.jpg`, `spec.pdf`, `README.md`)
- **Preserve mode**: Files are uploaded to matching S3 subfolders:
  ```
  project/
  ├── images/logo.png
  ├── images/banner.jpg
  ├── documents/spec.pdf
  └── README.md
  ```

## Error Handling

S3U provides robust error handling during uploads.

### Common Upload Errors

S3U handles these common issues:

1. **Missing AWS credentials**: Detected and reported with clear instructions
2. **Insufficient permissions**: Identified with explanatory error messages
3. **Network interruptions**: Individual file failures don't stop the entire batch
4. **File access issues**: Reported with specific error details
5. **Invalid file types**: Filtered out before upload attempts

### Error Reporting

For each failed upload, S3U reports:
- The specific file that failed
- The nature of the error
- Suggestions for resolution when possible

Example:
```
Error uploading vacation_photo.jpg: AccessDenied - Access Denied (Service: Amazon S3)
```

### Continuing After Errors

S3U is designed to continue processing the upload batch even if individual files fail. This ensures that transient errors don't require restarting the entire process.

## Post-Upload Actions

After uploading files, S3U performs these actions:

### URL Generation

S3U generates CloudFront URLs for all uploaded files:

```
https://d1lbnboj0lfh6w.cloudfront.net/vacation_photos/beach_001.jpg
```

These URLs provide fast, edge-cached access to your content.

### Clipboard Integration

URLs are automatically copied to your clipboard in the format specified by your configuration:

1. **Array format** (default):
   ```json
   ["https://d1lbnboj0lfh6w.cloudfront.net/folder/file1.jpg", "https://d1lbnboj0lfh6w.cloudfront.net/folder/file2.jpg"]
   ```

2. **JSON format**:
   ```json
   {
     "folder": "vacation_photos",
     "count": 2,
     "timestamp": "2023-08-15T14:22:33.456789",
     "files": [
       {
         "url": "https://d1lbnboj0lfh6w.cloudfront.net/folder/file1.jpg",
         "filename": "file1.jpg",
         "s3_path": "folder/file1.jpg",
         "size": 245678,
         "last_modified": "2023-08-15T14:20:12.345678",
         "type": "jpg"
       },
       ...
     ]
   }
   ```

3. **Other formats**: XML, HTML, or CSV as configured

### First-URL-Only Option

For single file uploads or when you only need the first URL:

```bash
s3u -f
```

This copies only the first URL to the clipboard, useful for single-file workflows.

## Advanced Upload Options

S3U provides several advanced options for customizing the upload process:

### Media Optimization

Before uploading, S3U can optimize images and videos:

```bash
s3u -config optimize always
```

See the [Media Optimization](S3U-configuration-guide.md#media-optimization-options) section of the Configuration Guide for details.

### File Renaming

S3U offers flexible file renaming options:

```bash
s3u -config rename_mode prepend
```

See the [File Renaming](S3U-utility-functions-guide.md#file-renaming) section of the Utility Functions Guide for details.

### Custom Output Formats

Control how URLs are formatted and copied to the clipboard:

```bash
s3u -config format json
```

See the [Output Options](S3U-configuration-guide.md#output-options) section of the Configuration Guide for details.

## Technical Implementation

S3U's upload functionality is built on modern asynchronous Python:

### Core Components

1. **AsyncIO**: Powers concurrent operations
2. **AIOBoto3**: Async wrapper for AWS SDK
3. **Semaphores**: Control concurrency limits
4. **Progress Callbacks**: Provide real-time status updates

### Upload Process Flow

The upload process follows this sequence:

1. `upload_files()`: Main entry point that orchestrates the process
2. `rename_files()`: Prepares files with consistent naming (if enabled)
3. `ensure_s3_folder_exists()`: Creates the target folder if needed
4. `upload_with_semaphore()`: Wrapper function that enforces concurrency limits
5. `upload_file()`: Handles individual file uploads with progress tracking
6. `format_output()`: Formats the results for clipboard copying

## Best Practices

To get the most out of S3U's upload functionality:

### For Performance

1. **Optimize concurrency** based on your connection and file sizes
2. **Group similar file sizes** together in uploads when possible
3. **Use the appropriate subfolder mode** for your content structure
4. **Consider file count** - many small files often benefit from higher concurrency

### For Organization

1. **Use consistent folder naming** conventions
2. **Leverage rename prefixes** for easy identification
3. **Consider using preserve mode** for complex projects
4. **Group files by type** when appropriate

### For Workflow Integration

1. **Use JSON or XML output** when integrating with other tools
2. **Script multiple operations** with command-line options
3. **Set up persistent configuration** for your common use cases
4. **Use the -f flag** when uploading single files for sharing

## Troubleshooting

Common upload issues and solutions:

### "Access Denied" Errors

**Cause**: Insufficient IAM permissions
**Solution**: Verify your IAM policy includes:
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:PutObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::your-bucket-name",
    "arn:aws:s3:::your-bucket-name/*"
  ]
}
```

### Slow Uploads

**Cause**: Network limitations or excessive concurrency
**Solution**:
- Reduce concurrency with `s3u -c 5`
- Check your network connection
- Consider optimizing large media files before upload

### Failed Uploads with Timeout

**Cause**: Network interruptions or very large files
**Solution**:
- Reduce concurrency
- Try uploading files individually
- Check for firewall or proxy issues

### "No Files to Upload" Message

**Cause**: No matching files or incorrect extension filter
**Solution**:
- Check the file extensions you specified
- Verify files exist in the current directory
- Try using `all` for extensions to include all files

### CloudFront URLs Not Working

**Cause**: CloudFront distribution not properly configured or deployed
**Solution**:
- Verify your CloudFront distribution is enabled
- Check the Origin settings in CloudFront
- Wait for CloudFront propagation (can take 15-30 minutes)

---

By mastering S3U's upload capabilities, you can efficiently manage your S3 content with minimal effort. The tool's flexible options accommodate a wide range of workflows, from simple one-off uploads to complex media management systems.
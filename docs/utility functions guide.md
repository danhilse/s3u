# S3U Utility Functions Guide

Beyond its core uploading capabilities, S3U provides several utility functions for file management, folder operations, and content retrieval. This guide covers the non-uploading functionality in the S3U tool.

## Table of Contents

- [File Selection and Filtering](#file-selection-and-filtering)
- [File Renaming](#file-renaming)
- [Folder Listing and Management](#folder-listing-and-management)
- [Content Downloading](#content-downloading)
- [Browsing and URL Generation](#browsing-and-url-generation)
- [MIME Type Handling](#mime-type-handling)
- [Command Line Interface](#command-line-interface)
- [Use Cases and Examples](#use-cases-and-examples)

## File Selection and Filtering

The `should_process_file` function determines which files to include in operations based on their extensions.

### How File Selection Works

Files are filtered using these rules:

1. If no extensions are specified, all files are included except:
   - Hidden files (starting with `.`)
   - System files like `.DS_Store`

2. When extensions are specified, only files matching those extensions are processed
   - Special handling exists for common types like JPG/JPEG

3. The following special cases are handled automatically:
   - `jpg` also matches `.jpeg` files
   - Video extensions like `mp4` and `mov` have dedicated handling

### Extension Examples

```bash
# Process only image files
s3u
Extensions: jpg png gif

# Process only video files
s3u
Extensions: mp4 mov

# Process documents
s3u
Extensions: pdf doc docx txt

# Process all files (default)
s3u
Extensions: all
```

### Extension Groups

S3U supports predefined extension groups:

- `images`: jpg, jpeg, png, gif, webp, svg
- `videos`: mp4, mov, avi, webm, mkv
- `documents`: pdf, doc, docx, txt, md

Example:
```bash
s3u
Extensions: images
```

## File Renaming

S3U can rename files before uploading using the `rename_files` function. This is useful for organizing files and creating consistent naming patterns.

### Renaming Options

There are three renaming modes:

1. **Replace mode** (`replace`): Original filenames are completely replaced with the pattern `prefix_index`
   - Example: `beach.jpg` → `vacation_001.jpg`

2. **Prepend mode** (`prepend`): The prefix is added before the original filename with the pattern `prefix_originalname`
   - Example: `beach.jpg` → `vacation_beach.jpg`

3. **Append mode** (`append`): The prefix is added after the original filename with the pattern `originalname_prefix`
   - Example: `beach.jpg` → `beach_vacation.jpg`

### Automatic Sequential Numbering

When using `replace` mode, files are automatically numbered with leading zeros based on the total number of files:

- 1-9 files: Single digit (e.g., `vacation_1.jpg`)
- 10-99 files: Two digits (e.g., `vacation_01.jpg`)
- 100-999 files: Three digits (e.g., `vacation_001.jpg`)
- 1000+ files: Four digits (e.g., `vacation_0001.jpg`)

This ensures proper alphabetical sorting in file listings.

### Setting Your Rename Mode

You can set your preferred rename mode in the configuration:

```bash
s3u -config rename_mode prepend
```

## Folder Listing and Management

S3U provides functions to list, browse, and manage folders in your S3 bucket.

### Listing All Folders

Use the `list_folders` function (via the `-ls` flag) to see all folders in your bucket with item counts:

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

This helps you:
- Get an overview of your bucket's organization
- See which folders contain the most items
- Find folders you might have forgotten about

### Folder Existence Checking

Before uploading, S3U automatically checks if the destination folder already exists using the `check_folder_exists` function. If it exists, you'll be prompted:

```
Folder 'vacation_photos' already exists in S3 bucket.
Include existing files in CDN links? (y/n) [y]: 
```

- Answering `y` includes both new and existing files in the output URLs
- Answering `n` includes only newly uploaded files

This helps prevent accidentally creating duplicate folders with slight name variations.

## Content Downloading

S3U allows you to download entire folders from your S3 bucket with the `download_folder` function.

### Basic Downloads

To download a folder:

```bash
s3u -d folder_name
```

This creates a local directory with the same name and downloads all files from the S3 folder.

### Advanced Download Options

You can customize downloads with additional options:

```bash
# Download only 5 files from a folder
s3u -d folder_name 5

# Download to a specific directory
s3u -d folder_name -o ./downloaded_files

# Download files recursively including subfolders
s3u -d folder_name -sf preserve
```

### Download Features

1. **Concurrent downloads**: Multiple files are downloaded simultaneously for speed
2. **Progress tracking**: Real-time progress is displayed with ETA
3. **Directory creation**: Destination directories are created if they don't exist
4. **Structure preservation**: Subfolder structures can be maintained
5. **Error handling**: Failed downloads are reported but don't stop the process

## Browsing and URL Generation

S3U includes functions to browse existing content and generate CloudFront URLs.

### Browsing Folders

To get CloudFront URLs for files in an existing folder:

```bash
s3u -b folder_name
```

This lists all objects in the folder and copies their URLs to your clipboard in the configured format.

### Limiting Results

You can limit the number of URLs returned:

```bash
s3u -b folder_name 12
```

This returns only the first 12 items (sorted alphabetically).

### Recursive Browsing

When using the preserve subfolder mode, browsing will recursively list all files including those in subfolders:

```bash
s3u -b folder_name -sf preserve
```

### URL Formats

The URLs are formatted according to your `format` configuration. For example:

- **Array format** (default):
  ```json
  ["https://d1lbnboj0lfh6w.cloudfront.net/folder/file1.jpg", "https://d1lbnboj0lfh6w.cloudfront.net/folder/file2.jpg"]
  ```

- **JSON format**:
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

## MIME Type Handling

S3U automatically determines the correct MIME type for files using the `get_mime_type` function.

### Supported MIME Types

S3U maps file extensions to appropriate MIME types:

| Extension | MIME Type |
|-----------|-----------|
| .jpg, .jpeg | image/jpeg |
| .png | image/png |
| .gif | image/gif |
| .webp | image/webp |
| .avif | image/avif |
| .mp4 | video/mp4 |
| .mov | video/quicktime |
| .webm | video/webm |
| .txt | text/plain |
| .html | text/html |
| .css | text/css |
| .js | application/javascript |
| .json | application/json |
| .pdf | application/pdf |
| .zip | application/zip |

For unlisted extensions, S3U uses the generic `application/octet-stream` type.

### Why MIME Types Matter

Correct MIME types ensure:
- Browsers handle files appropriately (e.g., playing videos instead of downloading them)
- CloudFront serves files with the correct `Content-Type` header
- Files can be properly indexed and categorized

## Command Line Interface

S3U's CLI provides direct access to these utility functions through dedicated flags:

| Flag | Function | Description |
|------|----------|-------------|
| `-ls` | `list_folders` | List all folders in the bucket with item counts |
| `-b FOLDER` | `list_s3_folder_objects` | Browse an existing folder and get URLs |
| `-d FOLDER` | `download_folder` | Download files from a folder |
| `-o DIR` | N/A | Specify output directory for downloads |
| `-sf MODE` | N/A | Set subfolder handling mode (ignore, pool, preserve) |
| `-f` | N/A | Copy only the first URL to clipboard |

## Use Cases and Examples

### Scenario 1: Content Inventory

Take inventory of your S3 bucket to see what's stored where:

```bash
# List all folders
s3u -ls

# Browse specific folders to check contents
s3u -b interesting_folder
```

### Scenario 2: Content Migration

Move files from one location to another:

```bash
# Download content from source folder
s3u -d source_folder -o ./migration

# Upload to new destination
cd ./migration
s3u
# Enter destination_folder when prompted
```

### Scenario 3: Folder Organization

Consolidate files from multiple subfolders:

```bash
# Create a directory structure
mkdir -p project/{images,videos,documents}

# Add files to each subfolder
# ...

# Upload preserving structure
s3u -sf preserve
# Enter "project" as the S3 folder name

# Or pool all files together
s3u -sf pool
# Enter "project_all" as the S3 folder name
```

### Scenario 4: Quick Access to Content

Get links to share with others:

```bash
# Get all links in HTML format
s3u -config format html
s3u -b portfolio_images

# Get just the first link
s3u -b latest_release -f
```

---

These utility functions make S3U a comprehensive tool for managing your S3 content beyond simple uploads. By leveraging these capabilities, you can create efficient workflows for content organization, sharing, and management.
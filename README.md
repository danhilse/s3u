# s3u - S3 Upload Utility

An interactive command-line tool for optimizing images, uploading files (including videos) to S3 with CloudFront URL generation.

## Features

- Interactive interface - no need to remember complex flags
- Tab completion for S3 folder names
- Image optimization using FFmpeg (three size options)
- Video file support (MP4, MOV)
- Filter files by extension
- Batch upload to S3 with async/concurrent uploads
- Automatic file renaming
- CloudFront URL generation
- Clipboard integration for easy URL sharing
- Browse existing S3 folders and get CDN links
- Download files from S3 folders with progress tracking
- List all folders with item counts
- Smart handling of existing folders
- Limit file counts for downloads and browsing
- Persistent configuration system with arrow key selection
- Multiple output formats (JSON, XML, HTML, CSV)

## Requirements

- Python 3.7+
- FFmpeg and FFprobe (for image optimization)
- AWS credentials configured in your environment

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/s3u.git
cd s3u

# Install the package
pip install -e .
```

## Usage

### Interactive Mode

Simply run the command and follow the interactive prompts:

```bash
s3u
```

During the folder selection step, press Tab to see existing folders and autocomplete folder names.

### Command Line Options

```bash
# Upload with 15 concurrent connections
s3u -c 15

# Get all CDN links from an existing folder in the bucket
s3u -b mj_watercolors

# Get only 12 CDN links from a folder
s3u -b mj_watercolors 12

# List all folders in the bucket with item counts
s3u -ls

# Download all files from a folder
s3u -d mj_watercolors

# Download only 5 files from a folder
s3u -d mj_watercolors 5

# Download files to a specific directory
s3u -d mj_watercolors -o ./downloaded_images

# Download 10 files to a specific directory
s3u -d mj_watercolors 10 -o ./downloaded_images
```

### Configuration System

s3u includes a persistent configuration system that allows you to set default values for various options.

```bash
# Show current configuration
s3u -config

# Configure a specific option interactively using arrow keys
s3u -config format

# Set a specific option directly
s3u -config format json

# Show all configuration values
s3u -config show
```

#### Interactive Configuration

When configuring options interactively, you can use arrow keys to select from available options:

```
Configuring: format
Description: Output format for generated URLs
Current value: array
Use arrow keys to select an option, Enter to confirm:
❯ array
  json
  xml
  html
  csv
```

Simply navigate to your preferred option using arrow keys and press Enter to select it.

#### Available Configuration Options

| Option | Description | Allowed Values | Default |
|--------|-------------|----------------|---------|
| format | Output format for generated URLs | array, json, xml, html, csv | array |
| concurrent | Default number of concurrent uploads | 1-20 | 5 |
| optimize | Default image optimization setting | auto, always, never | auto |
| size | Default optimization size | optimized, small, tiny | optimized |

#### Output Formats

The configuration system introduces multiple output formats for the URLs and metadata:

- **array**: Simple JSON array of URLs (default)
- **json**: JSON object with metadata including file size, type, and timestamps
- **xml**: XML document with file metadata
- **html**: HTML document with clickable links
- **csv**: CSV file format with URL and metadata columns

### Interactive Options

1. **File extensions** - Specify which file types to include (e.g., "jpg png mp4 mov" or "jpg,png,mp4,mov")
2. **Image optimization** - Choose whether to optimize images before uploading (skipped for video files)
3. **Optimization size** - Select from three size options (1920px, 1080px, or 640px)
4. **S3 folder** - Specify the destination folder in your S3 bucket (press Tab for autocompletion)
5. **Existing folder handling** - Choose whether to include existing files in CDN links (if folder exists)
6. **Rename prefix** - Optionally rename files with a common prefix
7. **Output format** - Choose between output formats for clipboard
8. **Concurrency** - Optionally enable concurrent uploads for speed

## Folder Management

### Working with Existing Folders

When uploading to a folder that already exists, you'll be prompted:
```
Folder 'your_folder' already exists in S3 bucket.
Include existing files in CDN links? (y/n) [y]: 
```

- Answer "y" (default) to include all files (existing + new) in the clipboard output
- Answer "n" to include only the newly uploaded files in the clipboard output

### Tab Completion for Folders

When entering a folder name in interactive mode:
1. The system fetches all existing folder names from S3
2. Press Tab to see available folders that match what you've typed
3. Continue typing or press Tab again to cycle through options
4. This helps ensure you're using a consistent folder structure

### Downloading Folders

When downloading a folder:
- Progress is displayed with estimated time remaining
- Files maintain their structure and relative paths
- The local directory is created if it doesn't exist
- Optionally limit the number of files downloaded with `s3u -d folder_name 5`

### Browsing Folders

When browsing a folder:
- All CloudFront URLs are copied to the clipboard in the configured format
- Optionally limit the number of URLs with `s3u -b folder_name 12`

### Listing Folders

The `-ls` flag shows a table of all folders in your bucket with item counts:

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

## Configuration File

The configuration is stored in a JSON file at `~/.s3u/config.json`. You can edit this file directly if needed, but it's recommended to use the `-config` command to ensure proper validation.

Example configuration file:
```json
{
    "format": "json",
    "concurrent": 10,
    "optimize": "auto",
    "size": "optimized"
}
```

## Notes

- The tool uses AWS credentials from your environment
- Upload destination is fixed to the "dh.images" bucket
- CloudFront distribution URL is hardcoded to "https://d1lbnboj0lfh6w.cloudfront.net"
- Image optimization requires FFmpeg and FFprobe installed on your system
- Video files (MP4, MOV) are supported but not optimized
- Downloads and folder listings use the same AWS credentials and bucket settings
- When limiting file counts, files are processed in alphabetical order
- Tab completion requires the readline module, which is standard in most Python installations
- Configuration settings are stored in the user's home directory and persist between sessions
- Arrow key selection for configuration requires the questionary package (included in dependencies)
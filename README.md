# S3U - S3 Upload Utility

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An interactive command-line tool for optimizing images, uploading files to S3, and generating CloudFront URLs with advanced capabilities for media management.

<p align="center">
  <img src="https://user-images.githubusercontent.com/placeholder/s3u-logo.png" alt="S3U Logo" width="200"/>
</p>

## 🚀 Quick Start

```bash
# Install the package
pip install s3u

# First-time setup
s3u -setup

# Upload files (interactive mode)
s3u

# List all folders in your bucket
s3u -ls

# Download a folder
s3u -d folder_name
```

## 📖 Documentation

S3U comes with comprehensive documentation available at [https://danhilse.github.io/s3u/](https://danhilse.github.io/s3u/):

- [Getting Started](https://danhilse.github.io/s3u/getting-started/) - Complete overview of features and usage
- [Configuration](https://danhilse.github.io/s3u/configuration/) - Detailed settings explanations
- [Utility Functions](https://danhilse.github.io/s3u/utility-functions/) - Non-upload functionality
- [Core Uploading](https://danhilse.github.io/s3u/core-uploading/) - Detailed upload process explanation
- [API Reference](https://danhilse.github.io/s3u/reference/) - Technical reference for developers

## ✨ Features

### Core Functionality
- 🔄 **Interactive interface** - No need to remember complex flags
- 🖼️ **Image optimization** - Resize and compress images using FFmpeg
- 🎥 **Video support** - Upload and transcode video files (MP4, MOV)
- 📂 **Batch uploads** - Process multiple files with concurrent transfers
- 🔗 **CloudFront integration** - Generate CDN URLs automatically
- 📋 **Clipboard integration** - Copy URLs directly to clipboard

### Advanced Features
- 🔍 **Tab completion** for S3 folder names
- 📱 **Multiple output formats** (JSON, XML, HTML, CSV)
- 🗂️ **Subfolder handling** (ignore, pool, or preserve)
- 📥 **Folder downloads** with progress tracking
- 📋 **Browse existing content** and get CDN links
- 📊 **Folder listing** with item counts
- ⚙️ **Persistent configuration system** with arrow key selection

## 📋 Requirements

- Python 3.7+
- FFmpeg and FFprobe (for image and video optimization)
- AWS credentials configured in your environment

## 🛠️ Installation

### From PyPI (Recommended)

```bash
pip install s3u
```

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/s3u.git
cd s3u

# Install in development mode
pip install -e .
```

## 💻 Usage

### Interactive Mode

Simply run the command and follow the prompts:

```bash
s3u
```

S3U will guide you through:
1. Selecting file types to include
2. Optional image optimization
3. Destination folder selection (with tab completion)
4. File renaming options
5. Upload configuration

### Command Line Options

```bash
# Upload with 15 concurrent connections
s3u -c 15

# Get CDN links from a folder
s3u -b folder_name

# List all folders in your bucket
s3u -ls

# Download files from a folder
s3u -d folder_name

# Quick mode (uses default settings)
s3u -q
```

See the [Getting Started](https://danhilse.github.io/s3u/getting-started/) page for a complete list of command line options.

### Configuration System

S3U includes a persistent configuration system:

```bash
# Show current configuration
s3u -config

# Configure an option interactively
s3u -config format

# Set an option directly
s3u -config format json
```

#### Available Configuration Options

| Option | Description | Allowed Values | Default |
|--------|-------------|----------------|---------|
| format | Output format for URLs | array, json, xml, html, csv | array |
| concurrent | Number of concurrent uploads | 1-20 | 5 |
| optimize | Image optimization setting | auto, always, never | auto |
| size | Optimization size | optimized, small, tiny, patches | optimized |
| rename_mode | How to rename files | replace, prepend, append | replace |
| subfolder_mode | Subfolder handling | ignore, pool, preserve | ignore |
| image_format | Image output format | webp, jpg, avif | webp |
| video_format | Video output format | mp4, webm | mp4 |

See the [Configuration](https://danhilse.github.io/s3u/configuration/) page for detailed explanations.

## 🗂️ Working with Folders

### Subfolder Handling

S3U offers three modes for handling subfolders:

```bash
# Only upload files in the current directory
s3u -sf ignore

# Combine all files from subfolders
s3u -sf pool

# Preserve the folder structure in S3
s3u -sf preserve
```

### Listing Folders

List all folders in your S3 bucket:

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

### Downloading Folders

Download content from S3:

```bash
# Download an entire folder
s3u -d folder_name

# Download to a specific location
s3u -d folder_name -o ./downloaded_images

# Limit the number of files
s3u -d folder_name 10
```

### Browsing Content

Get CloudFront URLs from existing folders:

```bash
# Get all URLs from a folder
s3u -b folder_name

# Get only 12 URLs
s3u -b folder_name 12

# Include files from subfolders
s3u -b folder_name -sf preserve
```

See the [Utility Functions](https://danhilse.github.io/s3u/utility-functions/) page for more folder operations.

## 🖼️ Media Optimization

S3U can optimize your images and videos before uploading:

### Image Optimization

Three size options are available:
- **optimized**: 1920px width (high quality)
- **small**: 1080px width (web quality)
- **tiny**: 640px width (thumbnail size)
- **patches**: 1280px width (high compression)

Supported output formats:
- **WebP**: Best compression-to-quality ratio
- **JPEG**: Maximum compatibility
- **AVIF**: Best compression (limited browser support)

### Video Optimization

For video files, S3U supports:
- Transcoding to MP4 (H.264) or WebM (VP9)
- Multiple encoding presets (fast, medium, slow)
- Resolution adjustment
- Optional audio removal (patches mode)

See the [Core Uploading](https://danhilse.github.io/s3u/core-uploading/) page for detailed optimization options.

## ⚙️ Configuration File

Settings are stored in `~/.s3u/config.json`. It's recommended to use the `-config` command rather than editing directly.

Example configuration file:
```json
{
    "format": "json",
    "concurrent": 10,
    "optimize": "auto",
    "size": "optimized",
    "rename_mode": "replace",
    "subfolder_mode": "ignore",
    "image_format": "webp",
    "video_format": "mp4",
    "bucket_name": "my-uploads",
    "cloudfront_url": "https://d1example.cloudfront.net"
}
```

## 📝 Notes

- S3U uses AWS credentials from your environment (via AWS CLI or environment variables)
- Image and video optimization requires FFmpeg and FFprobe
- Tab completion requires the readline module
- Arrow key selection for configuration requires the questionary package (included in dependencies)
- Files are processed in alphabetical order when limiting counts

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
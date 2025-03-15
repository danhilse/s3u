# S3U Configuration Guide

S3U includes a powerful configuration system that allows you to customize its behavior to match your workflow. This guide provides detailed information about each configuration option, how to use it, and how it affects S3U's functionality.

## Table of Contents

- [Configuration Basics](#configuration-basics)
  - [Viewing Configuration](#viewing-configuration)
  - [Modifying Configuration](#modifying-configuration)
  - [Configuration File](#configuration-file)
- [Output Options](#output-options)
  - [format](#format)
- [Performance Options](#performance-options)
  - [concurrent](#concurrent)
  - [max_workers](#max_workers)
- [Media Optimization Options](#media-optimization-options)
  - [optimize](#optimize)
  - [size](#size)
  - [image_format](#image_format)
  - [optimize_videos](#optimize_videos)
  - [video_format](#video_format)
  - [video_preset](#video_preset)
  - [remove_audio](#remove_audio)
- [File Management Options](#file-management-options)
  - [rename_mode](#rename_mode)
  - [subfolder_mode](#subfolder_mode)
- [AWS Configuration Options](#aws-configuration-options)
  - [aws_profile](#aws_profile)
  - [bucket_name](#bucket_name)
  - [cloudfront_url](#cloudfront_url)
  - [region](#region)
- [Example Configurations](#example-configurations)
  - [Photography Workflow](#photography-workflow)
  - [Web Development](#web-development)
  - [Video Production](#video-production)

## Configuration Basics

### Viewing Configuration

You can view your current configuration with:

```bash
s3u -config
```

This displays all configuration options, their current values, and descriptions.

### Modifying Configuration

There are two ways to modify configuration options:

**Interactive mode** (with arrow key selection if available):

```bash
s3u -config format
```

This allows you to select from available options using arrow keys.

**Direct setting**:

```bash
s3u -config format json
```

This immediately sets the option to the specified value.

### Configuration File

All settings are stored in `~/.s3u/config.json`. While you can edit this file directly, using the `-config` command is recommended as it validates your inputs.

Example configuration file:
```json
{
  "format": "json",
  "concurrent": 10,
  "optimize": "auto",
  "size": "optimized",
  "rename_mode": "replace",
  "image_format": "webp",
  "video_format": "mp4",
  "optimize_videos": "no",
  "video_preset": "medium",
  "max_workers": 4,
  "remove_audio": "no",
  "subfolder_mode": "ignore",
  "aws_profile": "",
  "bucket_name": "my-image-bucket",
  "cloudfront_url": "https://d1lbnboj0lfh6w.cloudfront.net",
  "region": "us-west-2",
  "setup_complete": true
}
```

## Output Options

### format

Controls the format of CloudFront URLs copied to your clipboard after upload or when browsing folders.

**Allowed Values**:
- `array` (default): Simple JSON array of URLs
- `json`: JSON object with detailed metadata
- `xml`: XML document with metadata
- `html`: HTML document with clickable links
- `csv`: CSV file with URLs and metadata

**Example Usage**:
```bash
s3u -config format json
```

**Effect**: When you upload files or browse folders with `s3u -b folder_name`, the output will be formatted according to this setting.

**When to Change**: 
- Use `array` for simplicity and easy integration with scripts
- Use `json` when you need detailed metadata about the files
- Use `html` when sharing links with non-technical users
- Use `csv` for importing into spreadsheets or data analysis tools
- Use `xml` for integration with systems that require XML

**JSON Format Example**:
```json
{
  "folder": "vacation_photos",
  "count": 2,
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
    {
      "url": "https://d1lbnboj0lfh6w.cloudfront.net/vacation_photos/sunset.jpg",
      "filename": "sunset.jpg",
      "s3_path": "vacation_photos/sunset.jpg",
      "size": 312456,
      "last_modified": "2023-08-15T14:21:45.678901",
      "type": "jpg"
    }
  ]
}
```

## Performance Options

### concurrent

Sets the default number of concurrent uploads to S3, affecting upload speed.

**Allowed Values**: 1-20 (default: 5)

**Example Usage**:
```bash
s3u -config concurrent 10
```

**Effect**: Controls how many files are uploaded simultaneously. Higher values can significantly speed up uploads of many small files, but may not help (or could even slow down) uploads of a few large files.

**When to Change**:
- Increase for faster uploads on high-bandwidth connections or when uploading many small files
- Decrease if you experience connection errors, timeouts, or have limited bandwidth
- For large files (videos or high-res images), a value of 3-5 is often optimal
- For many small files, values of 10-15 can improve throughput

You can also override this setting for a single session:
```bash
s3u -c 15
```

### max_workers

Controls the number of parallel workers used for media optimization.

**Allowed Values**: 1-16 (default: 4)

**Example Usage**:
```bash
s3u -config max_workers 8
```

**Effect**: Determines how many image or video optimization tasks run simultaneously. Higher values can speed up the optimization process but use more CPU and memory.

**When to Change**:
- Increase on systems with many CPU cores for faster optimization
- Decrease on systems with limited resources or if you experience slowdowns
- For video optimization, this setting is particularly important as transcoding is CPU-intensive

**Technical Details**: This setting only affects the optimization phase, not the upload phase. It determines the size of the thread pool used for the parallel processing of media files.

## Media Optimization Options

### optimize

Sets the default behavior for image optimization.

**Allowed Values**:
- `auto` (default): Ask during interactive mode
- `always`: Always optimize images without asking
- `never`: Never optimize images, just upload the originals

**Example Usage**:
```bash
s3u -config optimize always
```

**Effect**: Determines whether S3U will optimize images before uploading. Optimization can significantly reduce file sizes while maintaining visual quality.

**When to Change**:
- Set to `always` if you consistently want to optimize images
- Set to `never` if you prefer to use your own optimization tools or need to preserve the exact original files
- Leave as `auto` if you want to decide each time

### size

Determines the default size setting for image optimization.

**Allowed Values**:
- `optimized` (default): High quality (1920px max width)
- `small`: Medium quality (1080px max width)
- `tiny`: Low quality (640px max width)

**Example Usage**:
```bash
s3u -config size small
```

**Effect**: Controls the maximum dimensions and quality settings used when optimizing images. Smaller sizes result in smaller file sizes but lower image quality.

**When to Change**:
- Use `optimized` for high-quality images suitable for full-screen viewing
- Use `small` for web content and social media
- Use `tiny` for thumbnails or preview images

**Technical Details**: 
- If the original image is smaller than the maximum width, it won't be enlarged
- The height is automatically calculated to maintain the aspect ratio
- Quality settings are also adjusted based on the size to balance quality and file size

### image_format

Sets the default output format for optimized images.

**Allowed Values**:
- `webp` (default): Modern format with excellent compression
- `jpg`: Maximum compatibility
- `avif`: Best compression but limited browser support

**Example Usage**:
```bash
s3u -config image_format jpg
```

**Effect**: Determines the file format used when optimizing images. Different formats offer tradeoffs between file size, quality, and compatibility.

**When to Change**:
- Use `webp` for modern websites targeting recent browsers
- Use `jpg` when maximum compatibility is required
- Use `avif` for the smallest file sizes when browser support isn't a concern

**Technical Details**: 
- WebP offers ~30% smaller files than JPEG at equivalent quality
- AVIF offers ~50% smaller files than JPEG but has limited tool and browser support
- Format conversion happens during the optimization phase

### optimize_videos

Determines whether videos should be transcoded by default.

**Allowed Values**:
- `no` (default): Don't transcode videos
- `yes`: Transcode videos when optimizing

**Example Usage**:
```bash
s3u -config optimize_videos yes
```

**Effect**: Controls whether S3U will transcode video files during the optimization phase. Transcoding can reduce file sizes but takes longer and may reduce quality.

**When to Change**:
- Set to `yes` if you want to consistently optimize videos for web delivery
- Keep as `no` if you prefer to maintain original video quality or use your own transcoding tools

**Technical Details**: Video transcoding is CPU-intensive and can take significantly longer than image optimization. When enabled, videos are transcoded according to the `video_format` and `video_preset` settings.

### video_format

Sets the default output format for transcoded videos.

**Allowed Values**:
- `mp4` (default): Standard format with excellent compatibility
- `webm`: Better compression but less compatibility

**Example Usage**:
```bash
s3u -config video_format webm
```

**Effect**: Determines the container format and codec used when transcoding videos. MP4 uses H.264 codec, while WebM uses VP9.

**When to Change**:
- Use `mp4` for maximum compatibility across devices and browsers
- Use `webm` for better compression when targeting modern browsers

**Technical Details**: 
- MP4/H.264 is supported by virtually all devices and platforms
- WebM/VP9 offers better compression but isn't supported on older devices
- In pATCHES mode, MP4 is always used regardless of this setting

### video_preset

Controls the encoding speed/quality tradeoff for video transcoding.

**Allowed Values**:
- `fast`: Faster encoding, larger files
- `medium` (default): Balanced approach
- `slow`: Slower encoding, smaller files

**Example Usage**:
```bash
s3u -config video_preset slow
```

**Effect**: Determines the encoding preset used for video transcoding. Slower presets result in better compression (smaller files) at the cost of longer processing times.

**When to Change**:
- Use `fast` when you need quick results and file size is less important
- Use `medium` for a good balance between speed and file size
- Use `slow` when you want the smallest possible files and don't mind waiting longer

**Technical Details**: 
- This setting primarily affects the H.264 encoder for MP4 files
- For WebM files, it's translated to appropriate VP9 encoding settings
- In pATCHES mode, the `slow` preset is always used regardless of this setting

### remove_audio

Controls whether audio tracks should be removed from videos in pATCHES optimization mode.

**Allowed Values**:
- `no` (default): Keep audio tracks
- `yes`: Remove audio tracks

**Example Usage**:
```bash
s3u -config remove_audio yes
```

**Effect**: When using the pATCHES optimization mode for videos, this setting determines whether audio tracks are preserved or removed.

**When to Change**:
- Set to `yes` if you're creating video content that doesn't need audio
- Keep as `no` if audio is important for your videos

**Technical Details**: This setting only applies when using the pATCHES optimization mode for videos. Removing audio can further reduce file sizes, which can be beneficial for purely visual content.

## File Management Options

### rename_mode

Controls how rename prefixes are applied to filenames.

**Allowed Values**:
- `replace` (default): Replace original filenames with prefix + index
- `prepend`: Add prefix before original filename
- `append`: Add prefix after original filename

**Example Usage**:
```bash
s3u -config rename_mode prepend
```

**Effect**: Determines how filenames are transformed when using the rename prefix feature.

**When to Change**:
- Use `replace` for standardized sequential naming (e.g., vacation_001.jpg)
- Use `prepend` to categorize while preserving filenames (e.g., vacation_beach.jpg)
- Use `append` to add tags to filenames (e.g., beach_vacation.jpg)

**Examples with prefix "vacation"**:
- `replace`: Original file "beach.jpg" becomes "vacation_001.jpg"
- `prepend`: Original file "beach.jpg" becomes "vacation_beach.jpg"
- `append`: Original file "beach.jpg" becomes "beach_vacation.jpg"

### subfolder_mode

Determines how subfolders in the upload directory are handled.

**Allowed Values**:
- `ignore` (default): Only upload files in the main directory
- `pool`: Combine all files from subfolders into the main S3 folder
- `preserve`: Maintain the subfolder structure in S3

**Example Usage**:
```bash
s3u -config subfolder_mode preserve
```

**Effect**: Controls how S3U handles local subfolders when uploading files.

**When to Change**:
- Use `ignore` for simple uploads when only files in the current directory matter
- Use `pool` to collect files from all subfolders into a single S3 folder
- Use `preserve` to maintain your local folder structure in S3

**Technical Details**: 
- When using `preserve` mode, S3U creates matching folder structures in S3
- When using `pool` mode, all files are flattened into the main S3 folder, which may cause filename conflicts
- This setting can also be overridden for a single session:
  ```bash
  s3u -sf preserve
  ```

## AWS Configuration Options

### aws_profile

Specifies which AWS profile to use for S3 operations.

**Allowed Values**: Any profile name configured in your AWS credentials file (default: "" - use default profile)

**Example Usage**:
```bash
s3u -config aws_profile production
```

**Effect**: Determines which AWS credentials are used for S3 and CloudFront operations.

**When to Change**:
- When you need to use a specific AWS profile for uploading
- When working with multiple AWS accounts or environments

**Technical Details**: This setting uses the named profiles in your `~/.aws/credentials` file. Leave blank to use the default profile.

### bucket_name

Specifies the S3 bucket to use for all operations.

**Allowed Values**: Any valid S3 bucket name

**Example Usage**:
```bash
s3u -config bucket_name my-website-assets
```

**Effect**: Sets the destination bucket for uploads and the source bucket for downloads and browsing.

**When to Change**:
- When you need to switch between different S3 buckets
- Typically set during initial setup

**Technical Details**: You must have appropriate permissions for the specified bucket. The bucket must exist before you can use it with S3U.

### cloudfront_url

Sets the CloudFront distribution URL associated with your S3 bucket.

**Allowed Values**: Any valid CloudFront distribution URL

**Example Usage**:
```bash
s3u -config cloudfront_url https://d1example123.cloudfront.net
```

**Effect**: Used to generate CloudFront URLs for uploaded files.

**When to Change**:
- When you set up a new CloudFront distribution
- When you need to switch between different distributions
- Typically set during initial setup

**Technical Details**: The CloudFront distribution should be configured to use your S3 bucket as its origin.

### region

Specifies the AWS region for your S3 bucket.

**Allowed Values**: Any valid AWS region code (e.g., us-west-2, eu-central-1)

**Example Usage**:
```bash
s3u -config region eu-west-1
```

**Effect**: Sets the AWS region for S3 operations.

**When to Change**:
- When your S3 bucket is in a different region
- Typically set during initial setup

**Technical Details**: This setting is used for certain region-specific S3 operations. If not specified, S3U will try to determine the region from your AWS configuration.

## Example Configurations

### Photography Workflow

Optimized for photographers uploading large batches of images:

```bash
s3u -config format json
s3u -config concurrent 8
s3u -config optimize always
s3u -config size optimized
s3u -config image_format webp
s3u -config rename_mode replace
s3u -config max_workers 8
```

This configuration:
- Uses JSON output for detailed metadata
- Processes 8 uploads at a time for faster throughput
- Always optimizes images to a high-quality 1920px size
- Uses WebP format for excellent quality-to-size ratio
- Replaces original filenames with a consistent naming pattern
- Uses 8 parallel workers for faster optimization

### Web Development

Ideal for web developers preparing assets for websites:

```bash
s3u -config format html
s3u -config concurrent 10
s3u -config optimize always
s3u -config size small
s3u -config image_format webp
s3u -config rename_mode prepend
s3u -config subfolder_mode preserve
```

This configuration:
- Uses HTML output for easy sharing with clients
- Processes 10 uploads at a time for faster throughput
- Always optimizes images to a web-friendly 1080px size
- Uses WebP format for modern websites
- Prepends a prefix to original filenames to maintain context
- Preserves subfolder structure to maintain organization

### Video Production

Configured for video content creators:

```bash
s3u -config format json
s3u -config concurrent 3
s3u -config optimize always
s3u -config optimize_videos yes
s3u -config video_format mp4
s3u -config video_preset slow
s3u -config max_workers 12
```

This configuration:
- Uses JSON output for detailed metadata
- Limits concurrent uploads to 3 (since videos are large)
- Always optimizes media
- Enables video transcoding
- Uses MP4 format for maximum compatibility
- Uses the slow preset for better compression
- Allocates 12 workers for faster video processing
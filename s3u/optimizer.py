#!/usr/bin/env python3

import os
import subprocess
import sys
import concurrent.futures
from pathlib import Path

def get_media_info(input_path):
    """
    Get detailed information about a media file (image or video).
    
    Args:
        input_path (str): Path to the media file
        
    Returns:
        dict: Media information including type, width, height, codec, etc.
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-count_packets', '-show_entries', 'stream=width,height,codec_name,duration',
        '-of', 'json',
        input_path
    ]
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        import json
        data = json.loads(result.stdout)
        
        if 'streams' in data and len(data['streams']) > 0:
            stream = data['streams'][0]
            width = int(stream.get('width', 0))
            height = int(stream.get('height', 0))
            codec = stream.get('codec_name', '').lower()
            duration = float(stream.get('duration', 0))
            
            # Determine if it's an image or video
            is_image = codec in ['mjpeg', 'png', 'jpeg', 'jpg', 'gif']
            is_video = not is_image and codec in ['h264', 'hevc', 'vp9', 'av1', 'mpeg4', 'theora']
            
            return {
                'width': width,
                'height': height,
                'codec': codec,
                'duration': duration,
                'is_image': is_image,
                'is_video': is_video
            }
    except subprocess.CalledProcessError as e:
        print(f"Error getting info for {input_path}:")
        print(e.stderr)
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")
    
    return None

def optimize_image(input_path, output_path, max_width, quality, output_format='webp'):
    """
    Optimize an image with the specified parameters.
    
    Args:
        input_path (str): Path to the input image
        output_path (str): Path to save the optimized image
        max_width (int): Maximum width in pixels
        quality (int): Quality level (1-31 for webp, 1-100 for jpg/avif)
        output_format (str): Output format ('jpg', 'webp', or 'avif')
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get image dimensions
    width, height = get_image_size(input_path)
    if width is None or height is None:
        return False

    # Determine the scale filter
    scale_filter = f'scale={max_width}:-1'
    
    # If the original width is smaller than max_width, keep original size
    if width <= max_width:
        scale_filter = f'scale={width}:-1'
    
    # Set format-specific parameters
    if output_format == 'webp':
        # For WebP, quality is 0-100 (higher is better)
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', scale_filter,
            '-c:v', 'libwebp',
            '-quality', str(quality),
            '-y',
            output_path
        ]
    elif output_format == 'avif':
        # For AVIF, use libavif with crf (lower is better quality, 0-63)
        avif_crf = max(0, min(63, 63 - int(quality * 0.63)))  # Convert quality to CRF scale
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', scale_filter,
            '-c:v', 'libsvtav1',
            '-crf', str(avif_crf),
            '-y',
            output_path
        ]
    else:  # Default to jpg
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', scale_filter,
            '-c:v', 'mjpeg',
            '-q:v', str(quality),
            '-y',
            output_path
        ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        else:
            print(f"Error: Output file {output_path} is empty or doesn't exist")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error processing {input_path}:")
        print(e.stderr)
        return False
    
    return True

def get_image_size(input_path):
    """
    Get the dimensions of an image using ffprobe.
    
    Args:
        input_path (str): Path to the image
        
    Returns:
        tuple: (width, height) or (None, None) if an error occurs
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-count_packets', '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0',
        input_path
    ]
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        width, height = map(int, result.stdout.strip().split(','))
        return width, height
    except subprocess.CalledProcessError as e:
        print(f"Error getting size of {input_path}:")
        print(e.stderr)
        return None, None

def transcode_video(input_path, output_path, max_width, preset, video_format='mp4', bitrate=None, patches_mode=False, remove_audio=False):
    """
    Transcode a video to a web-optimized format.
    
    Args:
        input_path (str): Path to the input video
        output_path (str): Path to save the transcoded video
        max_width (int): Maximum width in pixels
        preset (str): Encoding preset ('fast', 'medium', 'slow')
        video_format (str): Output format ('mp4', 'webm')
        bitrate (str): Optional custom bitrate (e.g., '2M', '5M')
        patches_mode (bool): Whether to use the pATCHES optimization mode
        remove_audio (bool): Whether to remove audio from the video
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get video dimensions
    info = get_media_info(input_path)
    if info is None or not info.get('is_video', False):
        return False

    width, height = info['width'], info['height']
    
    # For pATCHES mode, use the specific scaling logic
    if patches_mode:
        # Scale to specified width while maintaining aspect ratio
        scale_filter = f"scale='min({max_width},iw)':-2"
    else:
        # Standard scaling logic
        if width <= max_width:
            scale_filter = f'scale={width}:-1'
        else:
            scale_filter = f'scale={max_width}:-1'
    
    # pATCHES optimization mode (higher compression settings)
    if patches_mode:
        # Always use MP4 with H.264 for pATCHES mode
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', scale_filter,
            '-c:v', 'libx264',
            '-crf', '28',           # Higher compression quality (higher CRF = more compression)
            '-preset', 'slow',      # Slow preset for better compression
        ]
        
        # Handle audio based on remove_audio flag
        if remove_audio:
            cmd.extend(['-an'])     # Remove audio
        else:
            cmd.extend([
                '-c:a', 'aac',      # Use AAC for audio
                '-b:a', '128k',     # Set audio bitrate to 128k
            ])
            
        # Add output path and movflags for web streaming
        cmd.extend([
            '-movflags', '+faststart',
            '-y',
            output_path
        ])
    # Standard optimization modes
    elif video_format == 'webm':
        # For WebM, use VP9
        codec = 'libvpx-vp9'
        if not bitrate:
            # Auto bitrate based on resolution
            if max_width <= 640:
                bitrate = '1M'
            elif max_width <= 1080:
                bitrate = '2M'
            else:
                bitrate = '4M'
                
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', scale_filter,
            '-c:v', codec,
            '-b:v', bitrate,
            '-c:a', 'libopus',
            '-speed', '1' if preset == 'slow' else '2' if preset == 'medium' else '4',
            '-y',
            output_path
        ]
    else:  # Default to MP4 with H.264
        codec = 'libx264'
        if not bitrate:
            # Auto bitrate based on resolution
            if max_width <= 640:
                bitrate = '1M'
            elif max_width <= 1080:
                bitrate = '2M'
            else:
                bitrate = '4M'
                
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', scale_filter,
            '-c:v', codec,
            '-b:v', bitrate,
            '-c:a', 'aac',
            '-preset', preset,
            '-movflags', '+faststart',  # For web streaming
            '-y',
            output_path
        ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        else:
            print(f"Error: Output file {output_path} is empty or doesn't exist")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error processing {input_path}:")
        print(e.stderr)
        return False
    
    return True

def process_file(file_data):
    """
    Process a single file (image or video) for parallel execution.
    
    Args:
        file_data (tuple): (input_path, output_path, options)
        
    Returns:
        tuple: (success, input_path, output_path)
    """
    input_path, output_path, options = file_data
    
    # Get file information
    input_lower = input_path.lower()
    
    # Check if it's an image or video
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff')
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v')
    
    if any(input_lower.endswith(ext) for ext in image_extensions):
        # Process image
        max_width = options.get('max_width', 1920)
        quality = options.get('quality', 85)
        output_format = options.get('output_format', 'webp')
        
        # Adjust the output path based on the format
        if not output_path.lower().endswith(f'.{output_format}'):
            output_path = os.path.splitext(output_path)[0] + f'.{output_format}'
        
        success = optimize_image(input_path, output_path, max_width, quality, output_format)
        return (success, input_path, output_path if success else None)
    
    elif any(input_lower.endswith(ext) for ext in video_extensions):
        # Process video
        if not options.get('optimize_videos', False):
            # If optimize_videos is disabled, just return the original file
            return (False, input_path, None)
            
        max_width = options.get('max_width', 1920)
        preset = options.get('preset', 'medium')
        video_format = options.get('video_format', 'mp4')
        bitrate = options.get('bitrate', None)
        patches_mode = options.get('patches_mode', False)
        remove_audio = options.get('remove_audio', False)
        
        # If in pATCHES mode, force MP4 format
        if patches_mode:
            video_format = 'mp4'
            
        # Adjust the output path based on the format
        if not output_path.lower().endswith(f'.{video_format}'):
            output_path = os.path.splitext(output_path)[0] + f'.{video_format}'
        
        success = transcode_video(
            input_path, 
            output_path, 
            max_width, 
            preset, 
            video_format, 
            bitrate, 
            patches_mode,
            remove_audio
        )
        return (success, input_path, output_path if success else None)
    
    return (False, input_path, None)

def process_directory(directory, options=None):
    """
    Optimize images and videos in the given directory with parallel processing.
    
    Args:
        directory (str): Directory containing media to process
        options (dict): Processing options including:
            - size (str): Which size to process ('optimized', 'small', or 'tiny')
            - output_format (str): Image output format ('jpg', 'webp', 'avif')
            - video_format (str): Video output format ('mp4', 'webm')
            - optimize_videos (bool): Whether to transcode videos
            - preset (str): Video encoding preset ('fast', 'medium', 'slow')
            - max_workers (int): Maximum number of concurrent workers
    
    Returns:
        tuple: (output_dir, processed_files) - the directory containing optimized media 
               and the list of processed file paths
    """
    if options is None:
        options = {}
    
    # Set default options
    size = options.get('size', 'optimized')
    output_format = options.get('output_format', 'webp')
    video_format = options.get('video_format', 'mp4')
    optimize_videos = options.get('optimize_videos', False)
    preset = options.get('preset', 'medium')
    max_workers = options.get('max_workers', min(os.cpu_count() or 1, 4))
    
    # Determine which size to process and set appropriate parameters
    if size == 'small':
        output_dir = os.path.join(os.path.abspath(directory), 'optimized', 'small')
        max_width = 1080
        quality = 80 if output_format == 'webp' else 3
    elif size == 'tiny':
        output_dir = os.path.join(os.path.abspath(directory), 'optimized', 'tiny')
        max_width = 640
        quality = 75 if output_format == 'webp' else 4
    elif size == 'patches':
        output_dir = os.path.join(os.path.abspath(directory), 'optimized', 'patches')
        max_width = 1280
        quality = 65 if output_format == 'webp' else 6  # Higher compression for images
        # For videos, we'll apply special settings in the transcode_video function
        options['patches_mode'] = True  # Flag to use special settings for videos
    else:  # Default to 'optimized'
        output_dir = os.path.join(os.path.abspath(directory), 'optimized')
        max_width = 1920
        quality = 85 if output_format == 'webp' else 2
        size = 'optimized'  # Normalize the size value

    # Create output directory
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {output_dir}: {e}")
        return None, []
    
    # Find media files to process
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff')
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v')
    
    files_to_process = []
    current_dir = os.path.abspath(directory)
    
    for filename in os.listdir(current_dir):
        if not os.path.isfile(os.path.join(current_dir, filename)):
            continue
            
        file_lower = filename.lower()
        file_path = os.path.join(current_dir, filename)
        
        # Determine output filename and extension
        base_name = os.path.splitext(filename)[0]
        
        if any(file_lower.endswith(ext) for ext in image_extensions):
            # Use the appropriate extension based on format
            if output_format == 'webp':
                output_filename = f"{base_name}.webp"
            elif output_format == 'avif':
                output_filename = f"{base_name}.avif"
            else:
                output_filename = f"{base_name}.jpg"
                
            output_path = os.path.join(output_dir, output_filename)
            
            # Image processing options
            process_options = {
                'max_width': max_width,
                'quality': quality,
                'output_format': output_format
            }
            
            files_to_process.append((file_path, output_path, process_options))
        
        elif optimize_videos and any(file_lower.endswith(ext) for ext in video_extensions):
            # Use the appropriate extension for videos
            output_filename = f"{base_name}.{video_format}"
            output_path = os.path.join(output_dir, output_filename)
            
            # Video processing options
            process_options = {
                'max_width': max_width,
                'preset': preset,
                'video_format': video_format,
                'optimize_videos': True
            }
            
            files_to_process.append((file_path, output_path, process_options))
    
    if not files_to_process:
        print(f"No media files found in directory to process with current settings")
        return output_dir, []
    
    # Process files in parallel
    processed_files = []
    
    print(f"Processing {len(files_to_process)} files using {max_workers} parallel workers...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(process_file, file_data): file_data for file_data in files_to_process}
        
        # Process results as they complete
        for i, future in enumerate(concurrent.futures.as_completed(future_to_file), 1):
            file_data = future_to_file[future]
            input_path = file_data[0]
            filename = os.path.basename(input_path)
            
            try:
                success, _, output_path = future.result()
                if success:
                    processed_files.append(output_path)
                    print(f"[{i}/{len(files_to_process)}] ✓ Processed: {filename}")
                else:
                    print(f"[{i}/{len(files_to_process)}] ✗ Failed to process: {filename}")
            except Exception as e:
                print(f"[{i}/{len(files_to_process)}] ✗ Error processing {filename}: {str(e)}")
    
    print(f"\nMedia optimization complete for directory: {directory}")
    print(f"Results can be found in: {output_dir}")
    print(f"Successfully processed {len(processed_files)} of {len(files_to_process)} files")
    
    return output_dir, processed_files
#!/usr/bin/env python3

import os
import subprocess
import sys

def get_image_size(input_path):
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

def optimize_image(input_path, output_path, max_width, quality):
    width, height = get_image_size(input_path)
    if width is None or height is None:
        return False

    # Use -1 to let FFmpeg automatically calculate the height while preserving aspect ratio
    scale_filter = f'scale={max_width}:-1'
    
    # If the original width is smaller than max_width, keep original size
    if width <= max_width:
        scale_filter = f'scale={width}:-1'

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
        if result.returncode == 0:
            # Verify the output file exists and has size > 0
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

def process_directory(directory, size='optimized'):
    """
    Optimize images in the given directory.
    
    Args:
        directory (str): Directory containing images to optimize
        size (str): Which size to process ('optimized', 'small', or 'tiny')
    
    Returns:
        tuple: (output_dir, file_paths) - the directory containing optimized images and the list of optimized file paths
    """
    current_dir = os.path.abspath(directory)
    optimized_dir = os.path.join(current_dir, 'optimized')
    
    # Determine which size to process and set appropriate parameters
    if size == 'small':
        output_dir = os.path.join(optimized_dir, 'small')
        max_width = 1080
        quality = 3
    elif size == 'tiny':
        output_dir = os.path.join(optimized_dir, 'tiny')
        max_width = 640
        quality = 4
    else:  # Default to 'optimized'
        output_dir = optimized_dir
        max_width = 1920
        quality = 2
        size = 'optimized'  # Normalize the size value

    # Create only the needed output directory
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {output_dir}: {e}")
        return None, []

    # Process images
    image_extensions = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
    processed_files = []
    
    for filename in os.listdir(current_dir):
        if filename.lower().endswith(image_extensions):
            input_path = os.path.join(current_dir, filename)
            output_filename = os.path.splitext(filename)[0] + '.jpg'
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"Processing {filename} for {size} size...")
            
            if optimize_image(input_path, output_path, max_width, quality):
                print(f"✓ Created {size} version: {output_filename}")
                processed_files.append(output_path)
            else:
                print(f"✗ Failed to process: {filename}")

    print(f"\nImage optimization complete for directory: {directory}")
    print(f"Results can be found in: {output_dir}")
    
    return output_dir, processed_files
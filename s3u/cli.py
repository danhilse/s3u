#!/usr/bin/env python3

import os
import sys
import argparse
import asyncio
import readline

# Import functions from core modules
from .core import (
    upload_files, 
    list_s3_folder_objects, 
    check_folder_exists, 
    download_folder,
    list_folders
)

# Import optimizer
from .optimizer import process_directory as optimize_images

# Import config functions
from .config import load_config, handle_config_command

def setup_folder_completion(folders):
    """
    Set up tab completion for folder names.
    
    Args:
        folders (list): List of folder names to use for completion
    """
    # Sort folders for consistent completion
    folders.sort()
    
    def complete_folder(text, state):
        """Tab completion function for folder names."""
        # Generate a list of matches
        matches = [folder for folder in folders if folder.startswith(text)]
        
        if state < len(matches):
            return matches[state]
        else:
            return None
    
    # Configure readline
    readline.set_completer(complete_folder)
    
    # Set the completion delimiters
    # Tab completion will only be applied to the text before these delimiters
    readline.set_completer_delims(' \t\n;')
    
    # Use the tab key for completion
    readline.parse_and_bind('tab: complete')

def get_input_with_completion(prompt, default=None, completion_list=None):
    """
    Get user input with optional tab completion.
    
    Args:
        prompt (str): Prompt to display to the user
        default (str): Default value if the user doesn't enter anything
        completion_list (list): List of values to use for tab completion
    
    Returns:
        str: User input or default value
    """
    # Set up completion if a completion list was provided
    if completion_list:
        setup_folder_completion(completion_list)
    
    # Format the prompt
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    # Get user input
    value = input(full_prompt).strip()
    
    # Disable completion after input to prevent interference with other inputs
    readline.set_completer(None)
    
    return value if value else default

def get_input(prompt, default=None):
    """Get user input with an optional default value."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    value = input(prompt).strip()
    return value if value else default

def parse_extensions(extensions_input):
    """Parse comma or space separated extensions."""
    if not extensions_input:
        return None
    
    # Handle both comma-separated and space-separated inputs
    if ',' in extensions_input:
        return [ext.strip() for ext in extensions_input.split(',') if ext.strip()]
    else:
        return [ext.strip() for ext in extensions_input.split() if ext.strip()]

def main():
    # Load configuration
    config = load_config()
    
    # Create argument parser for optional command line arguments
    parser = argparse.ArgumentParser(description="Upload files to S3 bucket with optional renaming.")
    parser.add_argument("-c", "--concurrent", type=int, help="Maximum concurrent uploads")
    parser.add_argument("-b", "--browse", metavar="FOLDER", help="Get CDN links from an existing folder in the bucket")
    parser.add_argument("-d", "--download", metavar="FOLDER", help="Download all files from a folder in the bucket")
    parser.add_argument("-o", "--output", metavar="DIR", help="Output directory for downloads (used with -d)")
    parser.add_argument("-ls", "--list", action="store_true", help="List all folders in the bucket with item count")
    parser.add_argument("-config", nargs="*", metavar="OPTION [VALUE]", help="Configure persistent settings (use without args to show all options)")
    parser.add_argument("count", nargs="?", type=int, help="Optional number of files to process (for -b or -d)")
    args = parser.parse_args()
    
    # Handle configuration command
    if hasattr(args, 'config') and args.config is not None:
        return handle_config_command(args.config)

    # If list flag is provided, list all folders and exit
    if args.list:
        print("Listing all folders in the bucket...")
        folders = asyncio.run(list_folders())
        if folders:
            print("\nFolders in S3 bucket:")
            print("-" * 50)
            print(f"{'Folder Name':<40} {'Items':<10}")
            print("-" * 50)
            for folder, count in sorted(folders):
                print(f"{folder:<40} {count:<10}")
            print("-" * 50)
            print(f"Total: {len(folders)} folders")
        else:
            print("No folders found or error listing folders.")
        return

    # If download flag is provided, download the folder and exit
    if args.download:
        folder = args.download
        output_dir = args.output if args.output else folder
        count = args.count  # This might be None, which means download all
        
        if count:
            print(f"Downloading {count} files from folder '{folder}' to '{output_dir}'...")
        else:
            print(f"Downloading all files from folder '{folder}' to '{output_dir}'...")
            
        asyncio.run(download_folder(folder, output_dir, count))
        return

    # If browse flag is provided, just get the CDN links and exit
    if args.browse:
        folder = args.browse
        count = args.count  # This might be None, which means list all
        
        if count:
            print(f"Getting {count} CDN links from folder: {folder}")
        else:
            print(f"Getting all CDN links from folder: {folder}")
            
        asyncio.run(list_s3_folder_objects(folder, return_urls_only=False, limit=count))
        return

    # Get current directory name as default folder name
    current_dir = os.path.basename(os.path.abspath('.'))
    
    # Interactive prompts
    print("S3 Upload Utility")
    print("-----------------")
    
    # Get file extensions
    extensions_input = get_input("File extensions to include (e.g., jpg png mp4 mov or jpg,png,mp4,mov)")
    extensions = parse_extensions(extensions_input)
    
    # Check if only video extensions are specified
    only_videos = False
    if extensions:
        video_extensions = ['mp4', 'mov']
        only_videos = all(ext.lower() in video_extensions for ext in extensions)
    
    # Ask about optimization based on config setting
    optimize = False
    optimize_size = None
    optimized_files = None
    source_dir = '.'


    # Use config setting for optimize
    optimize_config = config.get('optimize', 'auto')

    if optimize_config == 'always':
        optimize = True
        print("Media optimization enabled (based on config)")
    elif optimize_config == 'never':
        optimize = False
        print("Media optimization disabled (based on config)")
    else:  # 'auto'
        optimize = get_input("Optimize media before uploading? (y/n)", "n").lower() == 'y'

    if optimize:
        # Get default size from config
        default_size = config.get('size', 'optimized')
        
        # Ask which optimization size to use
        size_options = {
            '1': 'optimized',  # 1920px
            '2': 'small',      # 1080px
            '3': 'tiny',       # 640px
            '4': 'patches'     # 1280px with higher compression
        }
        
        # Determine the default choice based on the config
        default_choice = '1'  # Default to 'optimized'
        for choice, size in size_options.items():
            if size == default_size:
                default_choice = choice
        
        size_choice = get_input(f"Select size (1=optimized [1920px], 2=small [1080px], 3=tiny [640px], 4=pATCHES [1280px, high compression])", default_choice)
        optimize_size = size_options.get(size_choice, default_size)
        
        # Get image format preference
        default_image_format = config.get('image_format', 'webp')
        image_format_options = {
            '1': 'webp',  # WebP (good balance)
            '2': 'jpg',   # JPEG (most compatible)
            '3': 'avif'   # AVIF (best compression)
        }
        
        # Map config format to option number
        default_format_choice = '1'  # Default to WebP
        for opt, fmt in image_format_options.items():
            if fmt == default_image_format:
                default_format_choice = opt
        
        format_prompt = "Image format (1=webp [recommended], 2=jpg [compatible], 3=avif [best compression])"
        image_format_choice = get_input(format_prompt, default_format_choice)
        image_format = image_format_options.get(image_format_choice, default_image_format)
        
        # Check if there are video files in the extensions
        video_extensions = ['mp4', 'mov', 'avi', 'mkv', 'webm']
        has_videos = not extensions or any(ext.lower() in video_extensions for ext in (extensions or []))
        
        # Video optimization options
        optimize_videos = False
        video_format = config.get('video_format', 'mp4')
        video_preset = config.get('video_preset', 'medium')
        remove_audio = False
        
        if has_videos:
            optimize_videos_default = config.get('optimize_videos', 'no')
            if optimize_videos_default == 'yes':
                optimize_videos = True
                print("Video optimization enabled (based on config)")
            else:
                optimize_videos_input = get_input("Optimize videos as well? (y/n)", "n")
                optimize_videos = optimize_videos_input.lower() == 'y'
            
            if optimize_videos:
                # Get video format preference
                default_video_format = config.get('video_format', 'mp4')
                video_format_options = {
                    '1': 'mp4',   # MP4/H.264 (compatible)
                    '2': 'webm'   # WebM/VP9 (better compression)
                }
                
                # Map config format to option number
                default_video_choice = '1'  # Default to MP4
                for opt, fmt in video_format_options.items():
                    if fmt == default_video_format:
                        default_video_choice = opt
                
                video_format_prompt = "Video format (1=mp4 [compatible], 2=webm [better compression])"
                video_format_choice = get_input(video_format_prompt, default_video_choice)
                video_format = video_format_options.get(video_format_choice, default_video_format)
                
                # Get video preset preference
                default_preset = config.get('video_preset', 'medium')
                preset_options = {
                    '1': 'fast',    # Fast encoding, larger files
                    '2': 'medium',  # Balanced
                    '3': 'slow'     # Slow encoding, smaller files
                }
                
                # Map config preset to option number
                default_preset_choice = '2'  # Default to medium
                for opt, preset in preset_options.items():
                    if preset == default_preset:
                        default_preset_choice = opt
                
                preset_prompt = "Video encoding preset (1=fast [quick], 2=medium [balanced], 3=slow [best quality])"
                preset_choice = get_input(preset_prompt, default_preset_choice)
                video_preset = preset_options.get(preset_choice, default_preset)
                
                # For pATCHES mode, ask about removing audio
                if optimize_size == 'patches':
                    remove_audio_default = config.get('remove_audio', 'no')
                    remove_audio_prompt = "Remove audio from videos? (y/n)"
                    remove_audio_input = get_input(remove_audio_prompt, "y" if remove_audio_default == "yes" else "n")
                    remove_audio = remove_audio_input.lower() == 'y'
        
        # Get number of optimization workers
        default_workers = config.get('max_workers', 4)
        workers_prompt = f"Parallel optimization workers (1-16, higher=faster) [{default_workers}]"
        workers_input = get_input(workers_prompt, str(default_workers))
        max_workers = int(workers_input) if workers_input.isdigit() and 1 <= int(workers_input) <= 16 else default_workers
        
        # Run optimization
        print("\nOptimizing media...")
        
        # Prepare options dictionary for optimizer
        optimization_options = {
            'size': optimize_size,
            'output_format': image_format,
            'video_format': video_format,
            'optimize_videos': optimize_videos,
            'preset': video_preset,
            'max_workers': max_workers,
            'remove_audio': remove_audio
        }
        
        # Pass the options to the optimizer
        source_dir, optimized_files = optimize_images('.', optimization_options)
        
        if not optimized_files:
            print("No files were optimized. Proceeding with regular upload.")
            source_dir = '.'
            optimized_files = None
        else:
            # Update the source directory to point to the optimized files
            print(f"Will upload {len(optimized_files)} optimized files from {source_dir}")

    
    # Get list of existing folders for tab completion
    print("Fetching existing folders for tab completion...")
    folder_tuples = asyncio.run(list_folders())
    existing_folders = [folder for folder, _ in folder_tuples]
    print(f"Found {len(existing_folders)} folders")
    
    # Get S3 folder with tab completion
    print("Enter folder name (press Tab to see existing folders)")
    folder = get_input_with_completion("S3 folder name", current_dir, existing_folders)
    
    # Check if folder exists in S3
    folder_exists = asyncio.run(check_folder_exists(folder))
    
    # Initialize include_existing with default value
    include_existing = True
    
    if folder_exists:
        print(f"\nFolder '{folder}' already exists in S3 bucket.")
        include_existing_input = get_input("Include existing files in CDN links? (y/n)", "y")
        include_existing = include_existing_input.lower() == 'y'
    
    # Get rename prefix
    rename_prefix = get_input("Rename prefix (optional, press Enter to skip)")
    
    # Get rename mode if a prefix is specified
    rename_mode = config.get('rename_mode', 'replace')  # Get default from config
    
    if rename_prefix:
        mode_options = {
            '1': 'replace',  # Replace filename with prefix_index
            '2': 'prepend',  # Prepend the prefix to filename (prefix_filename)
            '3': 'append',   # Append the prefix to filename (filename_prefix)
        }
        
        # Find default option based on config
        default_option = '1'  # Default to replace
        for opt, mode in mode_options.items():
            if mode == rename_mode:
                default_option = opt
                
        mode_prompt = "Rename mode (1=replace [prefix_index], 2=prepend [prefix_filename], 3=append [filename_prefix])"
        mode_choice = get_input(mode_prompt, default_option)
        selected_mode = mode_options.get(mode_choice, rename_mode)
    else:
        selected_mode = rename_mode  # Use config default, but it won't be used anyway
    
    # Get output format from config
    default_format = config.get('format', 'array')
    format_options = {
        '1': 'array',  # Default JSON array
        '2': 'json',   # JSON object with additional metadata
        '3': 'xml',    # XML format
        '4': 'html',   # HTML links
        '5': 'csv'     # CSV format
    }
    
    # Map config format to option number
    default_option = '1'  # Default to array
    for opt, fmt in format_options.items():
        if fmt == default_format:
            default_option = opt
    
    format_prompt = "Output format (1=array, 2=json, 3=xml, 4=html, 5=csv)"
    output_format = get_input(format_prompt, default_option)
    
    # Determine if we should only return the first URL based on the format
    selected_format = format_options.get(output_format, 'array')
    only_first = (output_format == "1" and default_format == "array")  # Legacy behavior
    
    # Get concurrency from config or command line
    concurrent = args.concurrent
    if not concurrent:
        # Use config value as default
        config_concurrent = config.get('concurrent', 5)
        concurrent_input = get_input(f"Concurrent uploads (optional, press Enter for {config_concurrent})")
        concurrent = int(concurrent_input) if concurrent_input else config_concurrent
    
    # Update the "Confirm settings" section with new information
    print("\nUpload Settings:")
    print(f"  Extensions: {extensions if extensions else 'All files'}")

    if optimize:
        print(f"  Media optimization: {optimize_size}")
        print(f"  Image format: {image_format}")
        
        if optimize_videos:
            print(f"  Video optimization: Enabled")
            print(f"  Video format: {video_format if optimize_size != 'patches' else 'mp4 (forced by pATCHES mode)'}")
            print(f"  Video preset: {video_preset if optimize_size != 'patches' else 'slow (forced by pATCHES mode)'}")
            if optimize_size == 'patches':
                print(f"  Remove audio: {'Yes' if remove_audio else 'No'}")
        else:
            print(f"  Video optimization: Disabled")
            
        print(f"  Parallel workers: {max_workers}")
    else:
        print("  Media optimization: Disabled")
    print(f"  S3 Folder: {folder}")
    if folder_exists:
        print(f"  Include Existing Files: {'Yes' if include_existing else 'No'}")
    if rename_prefix:
        print(f"  Rename Prefix: {rename_prefix}")
        print(f"  Rename Mode: {selected_mode}")
    else:
        print("  No renaming")
    print(f"  Output Format: {selected_format.capitalize()}")
    print(f"  Concurrent Uploads: {concurrent}")
    
    confirm = get_input("\nProceed with upload? (y/n)", "y")
    if confirm.lower() != 'y':
        print("Upload cancelled.")
        return
    
    # Run the upload
    asyncio.run(upload_files(
        s3_folder=folder,
        extensions=extensions,
        rename_prefix=rename_prefix,
        rename_mode=selected_mode,
        only_first=only_first,
        max_concurrent=concurrent,
        source_dir=source_dir,
        specific_files=optimized_files,
        include_existing=include_existing,
        output_format=selected_format  # Pass the selected format to uploader
    ))

if __name__ == "__main__":
    main()
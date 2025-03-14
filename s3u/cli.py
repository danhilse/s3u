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
    
    if not only_videos:
        # Use config setting for optimize
        optimize_config = config.get('optimize', 'auto')
        
        if optimize_config == 'always':
            optimize = True
            print("Image optimization enabled (based on config)")
        elif optimize_config == 'never':
            optimize = False
            print("Image optimization disabled (based on config)")
        else:  # 'auto'
            optimize = get_input("Optimize images before uploading? (y/n)", "n").lower() == 'y'
        
        if optimize:
            # Get default size from config
            default_size = config.get('size', 'optimized')
            
            # Ask which optimization size to use
            size_options = {
                '1': 'optimized',  # 1920px
                '2': 'small',      # 1080px
                '3': 'tiny'        # 640px
            }
            
            # Determine the default choice based on the config
            default_choice = '1'  # Default to 'optimized'
            for choice, size in size_options.items():
                if size == default_size:
                    default_choice = choice
            
            size_choice = get_input(f"Select size (1=optimized [1920px], 2=small [1080px], 3=tiny [640px])", default_choice)
            optimize_size = size_options.get(size_choice, default_size)
            
            # Run optimization
            print("\nOptimizing images...")
            source_dir, optimized_files = optimize_images('.', optimize_size)
            
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
    
    # Confirm settings
    print("\nUpload Settings:")
    print(f"  Extensions: {extensions if extensions else 'All files'}")
    if only_videos:
        print("  No optimization (video files only)")
    elif optimize:
        print(f"  Using optimized images ({optimize_size})")
    print(f"  S3 Folder: {folder}")
    if folder_exists:
        print(f"  Include Existing Files: {'Yes' if include_existing else 'No'}")
    print(f"  Rename Prefix: {rename_prefix if rename_prefix else 'No renaming'}")
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
        only_first=only_first,
        max_concurrent=concurrent,
        source_dir=source_dir,
        specific_files=optimized_files,
        include_existing=include_existing,
        output_format=selected_format  # Pass the selected format to uploader
    ))

if __name__ == "__main__":
    main()
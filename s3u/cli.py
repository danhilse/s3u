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

# Define common extension groups for easy selection
EXTENSION_GROUPS = {
    "images": ["jpg", "jpeg", "png", "gif", "webp", "svg"],
    "videos": ["mp4", "mov", "avi", "webm", "mkv"],
    "documents": ["pdf", "doc", "docx", "txt", "md"],
}

def parse_extensions(extensions_input):
    """
    Parse file extensions input and return a normalized list.
    
    Args:
        extensions_input (str): Input string with extensions
        
    Returns:
        list or None: List of normalized extensions or None for all files
    """
    # Check for empty input or explicit "all" keyword
    if not extensions_input or extensions_input.lower() == "all":
        return None  # None represents all files
    
    # Check if input is a predefined extension group
    if extensions_input.lower() in EXTENSION_GROUPS:
        return EXTENSION_GROUPS[extensions_input.lower()]
    
    # Replace commas with spaces for consistent splitting
    normalized_input = extensions_input.replace(',', ' ')
    
    # Split by spaces and normalize each extension
    extensions = []
    for ext in normalized_input.split():
        # Remove leading dots if present and convert to lowercase
        ext = ext.lstrip('.').lower().strip()
        if ext:  # Only add non-empty extensions
            extensions.append(ext)
    
    return extensions if extensions else None

def get_extensions_input():
    """Get file extensions with helpful suggestions."""
    print("\nFile extensions to include:")
    print("  • Enter 'all' or leave blank for all files (default)")
    print("  • Enter specific types separated by spaces or commas (e.g., 'jpg png mp4')")
    print("  • Or use one of these groups:")
    for group, exts in EXTENSION_GROUPS.items():
        print(f"    - {group}: {', '.join(exts)}")
    
    extensions_input = get_input("Extensions", "all")
    extensions = parse_extensions(extensions_input)
    
    # Provide feedback about what extensions will be used
    if extensions is None:
        print("Using all file types")
    elif extensions_input.lower() in EXTENSION_GROUPS:
        print(f"Using {extensions_input.lower()} group: {', '.join(extensions)}")
    else:
        print(f"Using extensions: {', '.join(extensions)}")
    
    return extensions

def scan_for_subfolders(directory):
    """
    Scan for subfolders in the given directory.
    
    Args:
        directory (str): The directory to scan
        
    Returns:
        list: List of subfolders found (relative paths)
    """
    subfolders = []
    for root, dirs, files in os.walk(directory):
        if root != directory:  # Skip the main directory
            # Get relative path
            relpath = os.path.relpath(root, directory)
            subfolders.append(relpath)
    
    return subfolders

async def get_bucket_name():
    """Get bucket name from config."""
    config = load_config()
    return config.get("bucket_name")

async def get_cloudfront_url():
    """Get CloudFront URL from config."""
    config = load_config()
    return config.get("cloudfront_url")

async def get_s3_session():
    """Get the AWS session for S3 operations."""
    # This would use credentials from ~/.aws/credentials or env vars
    # For this implementation we're just returning None as a placeholder
    return None

async def verify_permissions(session, bucket_name, cloudfront_url):
    """Verify the permissions for S3 operations."""
    # This would check if we can list, read, and write to the bucket
    # For this implementation we're just returning a placeholder
    return {
        's3_list': True,
        's3_read': True,
        's3_write': True
    }

async def run_setup():
    """Run the setup wizard to configure S3U."""
    print("Setting up s3u...")
    
    # Get bucket name
    bucket_name = input("Enter your S3 bucket name: ").strip()
    if not bucket_name:
        print("Error: Bucket name is required.")
        return
    
    # Get CloudFront URL (optional)
    cloudfront_url = input("Enter your CloudFront URL (optional): ").strip()
    
    # Save to config
    config = load_config()
    config["bucket_name"] = bucket_name
    if cloudfront_url:
        config["cloudfront_url"] = cloudfront_url
    config["setup_complete"] = True
    
    # Save config file
    from .config import save_config
    save_config(config)
    
    print("Setup complete! You can now use s3u.")

async def main():
    # Create argument parser for optional command line arguments FIRST
    parser = argparse.ArgumentParser(description="Upload files to S3 bucket with optional renaming.")
    parser.add_argument("-c", "--concurrent", type=int, help="Maximum concurrent uploads")
    parser.add_argument("-b", "--browse", metavar="FOLDER", help="Get CDN links from an existing folder in the bucket")
    parser.add_argument("-d", "--download", metavar="FOLDER", help="Download all files from a folder in the bucket")
    parser.add_argument("-o", "--output", metavar="DIR", help="Output directory for downloads (used with -d)")
    parser.add_argument("-ls", "--list", action="store_true", help="List all folders in the bucket with item count")
    parser.add_argument("-config", nargs="*", metavar="OPTION [VALUE]", help="Configure persistent settings (use without args to show all options)")
    parser.add_argument("-setup", action="store_true", help="Run the setup wizard to configure S3U")
    parser.add_argument("-q", "--quick", action="store_true", help="Quick mode: skip all prompts and use default settings with folder 'default'")
    parser.add_argument("count", nargs="?", type=int, help="Optional number of files to process (for -b or -d)")
    parser.add_argument("-f", "--first", action="store_true", help="Copy only the first URL to clipboard")
    parser.add_argument("-sf", "--subfolder-mode", choices=["ignore", "pool", "preserve"], 
                        help="How to handle subfolders: ignore, pool, or preserve")
    parser.add_argument("path", nargs="?", help="Path to the directory containing files to upload")
    args = parser.parse_args()
    
    # Check if quick mode is enabled
    quick_mode = args.quick
    
    # Handle the setup flag first
    if args.setup:
        from .setup import run_setup
        await run_setup(force=True)
        print("\nSetup completed. Run 's3u' again to use the tool.")
        return

    # Handle special commands next (config, list, browse, download)
    if args.config is not None:
        return handle_config_command(args.config)
    
    if args.list:
        return await list_folders()
    
    if args.browse:
        # Load config for format setting
        config = load_config()
        count = args.count or 0  # 0 means all files
        return await list_s3_folder_objects(args.browse, limit=count, output_format=config.get('format', 'array'))
    
    if args.download:
        count = args.count or 0  # 0 means all files
        output_dir = args.output or '.'
        return await download_folder(args.download, output_dir, limit=count)
    
    # Load configuration
    config = load_config()
    
    # Check if setup is complete - only after handling special commands
    if not config.get("setup_complete", False):
        print("Initial setup required. Running setup wizard...")
        from .setup import run_setup
        await run_setup()
        print("\nSetup complete! Run 's3u' again to start using the tool.")
        return
    
    # Get bucket name and CloudFront URL from config
    bucket_name = await get_bucket_name()
    cloudfront_url = await get_cloudfront_url()
    
    if not bucket_name:
        print("Error: S3 bucket not configured. Run 's3u -config bucket_name' to set it.")
        return
    
    # Verify permissions before proceeding
    session = await get_s3_session()
    permissions = await verify_permissions(session, bucket_name, cloudfront_url)
    
    if not all([permissions['s3_list'], permissions['s3_read'], permissions['s3_write']]):
        print("⚠️ Permission check failed. Some S3 operations may not work.")
        if input("Continue anyway? (y/n) [n]: ").lower() != 'y':
            return
    
    # Initialize only_first flag 
    only_first = False
    if args.first:
        only_first = True
    
    # Set the source directory from path argument if provided
    source_dir = '.'
    if args.path:
        source_dir = args.path
        
        # Strip quotes if present
        if (source_dir.startswith('"') and source_dir.endswith('"')) or \
           (source_dir.startswith("'") and source_dir.endswith("'")):
            source_dir = source_dir[1:-1]
            
        # Verify path exists
        if not os.path.isdir(source_dir):
            print(f"Error: Path does not exist or is not a directory: {source_dir}")
            return
        
        print(f"Using source directory: {source_dir}")
    
    # Change working directory to source_dir if it's different from current
    original_dir = os.getcwd()
    if source_dir != '.':
        try:
            os.chdir(source_dir)
            print(f"Changed working directory to: {os.getcwd()}")
        except Exception as e:
            print(f"Error changing directory: {str(e)}")
            return
    
    # Get current directory name as default folder name
    current_dir = os.path.basename(os.path.abspath('.'))
    
    # Use command line argument if provided, otherwise use config value
    # concurrent = args.concurrent or config.get('concurrent', 5)
    
    concurrent = args.concurrent or config.get('concurrent', 5)

    
    if quick_mode:
        print("S3 Upload Utility (Quick Mode)")
        print("-----------------------------")
        print("Using default settings...")
        
        # Use default values for all settings in quick mode
        extensions = None  # All files
        folder = "default"
        include_existing = False
        rename_prefix = ""
        subfolder_mode = args.subfolder_mode or config.get('subfolder_mode', 'ignore')
        
        # Use config settings for optimization
        optimize = config.get('optimize', 'auto') == 'always'
        optimize_size = config.get('size', 'optimized')
        image_format = config.get('image_format', 'webp')
        video_format = config.get('video_format', 'mp4')
        video_preset = config.get('video_preset', 'medium')
        optimize_videos = config.get('optimize_videos', 'no') == 'yes'
        max_workers = config.get('max_workers', 4)
        remove_audio = config.get('remove_audio', 'no') == 'yes'
        
        # Other settings from config
        rename_mode = config.get('rename_mode', 'replace')
        selected_format = config.get('format', 'array')
        
        # Prepare optimization options if optimization is enabled
        if optimize:
            optimization_options = {
                'size': optimize_size,
                'output_format': image_format,
                'video_format': video_format,
                'optimize_videos': optimize_videos,
                'preset': video_preset,
                'max_workers': max_workers,
                'remove_audio': remove_audio
            }
        else:
            optimization_options = None
        
        # Set confirm to 'y' to skip confirmation prompt
        confirm = 'y'
    else:
        print("S3 Upload Utility")
        print("-----------------")
        
        # Get file extensions
        extensions = get_extensions_input()
        
        # Check if only video extensions are specified
        only_videos = False
        if extensions:
            video_extensions = ['mp4', 'mov']
            only_videos = all(ext.lower() in video_extensions for ext in extensions)
        
        # Check for subfolders
        subfolders = scan_for_subfolders('.')
        has_subfolders = len(subfolders) > 0
        
        # Determine subfolder mode
        if args.subfolder_mode:
            # Use command line argument if provided
            subfolder_mode = args.subfolder_mode
            if has_subfolders:
                print(f"Using subfolder mode '{subfolder_mode}' from command line")
        elif has_subfolders:
            # If subfolders are found, ask how to handle them
            print(f"\nDetected {len(subfolders)} subfolders in the current directory:")
            for i, subfolder in enumerate(subfolders[:5], 1):  # Show first 5 only
                print(f"  {i}. {subfolder}")
            if len(subfolders) > 5:
                print(f"  ... and {len(subfolders) - 5} more")
            
            # Use config setting as default
            subfolder_mode_config = config.get('subfolder_mode', 'ignore')
            
            subfolder_options = {
                '1': 'ignore',   # Ignore subfolders
                '2': 'pool',     # Combine all files
                '3': 'preserve'  # Preserve structure
            }
            
            # Map config to option number
            default_option = '1'  # Default to ignore
            for opt, mode in subfolder_options.items():
                if mode == subfolder_mode_config:
                    default_option = opt
                    
            mode_prompt = "How to handle subfolders? (1=ignore, 2=pool all files, 3=preserve structure)"
            mode_choice = get_input(mode_prompt, default_option)
            subfolder_mode = subfolder_options.get(mode_choice, subfolder_mode_config)
            
            print(f"Subfolder mode: {subfolder_mode}")
        else:
            # Use the default from config
            subfolder_mode = config.get('subfolder_mode', 'ignore')
        
        # =============== OPTIMIZATION SETTINGS COLLECTION ===============
        
        optimize = False
        optimize_size = None
        image_format = None
        video_format = None
        video_preset = None
        optimize_videos = False
        max_workers = None
        remove_audio = False
        optimization_options = None
        
        if not only_videos:
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
                workers_prompt = f"Parallel optimization workers (1-16, higher=faster)"
                workers_input = get_input(workers_prompt, str(default_workers))
                max_workers = int(workers_input) if workers_input.isdigit() and 1 <= int(workers_input) <= 16 else default_workers
                
                # Prepare optimization options for later use
                optimization_options = {
                    'size': optimize_size,
                    'output_format': image_format,
                    'video_format': video_format,
                    'optimize_videos': optimize_videos,
                    'preset': video_preset,
                    'max_workers': max_workers,
                    'remove_audio': remove_audio
                }
        
        # =============== S3 UPLOAD SETTINGS COLLECTION ===============
        
        # Get S3 folder with tab completion - only fetch folders when needed
        print("Enter folder name (press Tab to see existing folders)")
        
        # Get the folder name first, without completion
        folder = get_input("S3 folder name", current_dir)
        
        # If the user pressed tab or seems to be looking for completion, then fetch folders
        if not folder or folder == current_dir:
            print("Fetching existing folders for tab completion...")
            folder_tuples = await list_folders()
            existing_folders = [folder for folder, _ in folder_tuples]
            print(f"Found {len(existing_folders)} folders")
            
            # Now get the folder with completion
            folder = get_input_with_completion("S3 folder name", folder, existing_folders)
        
        # Check if folder exists in S3
        folder_exists = await check_folder_exists(folder)
        
        # Initialize include_existing with default value
        include_existing = False
        
        if folder_exists:
            print(f"\nFolder '{folder}' already exists in S3 bucket.")
            include_existing_input = get_input("Include existing files in CDN links? (y/n)", "n")
            include_existing = include_existing_input.lower() == 'y'
        
        # Get rename prefix
        rename_prefix = get_input("Rename prefix (optional, press Enter to skip)")
        
        # Get rename mode and output format from config
        rename_mode = config.get('rename_mode', 'replace')
        selected_format = config.get('format', 'array')
        
        # Get final confirmation
        confirm = get_input("\nProceed with upload? (y/n)", "y")
    
    # =============== DISPLAY SETTINGS SUMMARY ===============
    
    print("\nUpload Settings:")
    if extensions is None:
        print(f"  Extensions: All files")
    else:
        print(f"  Extensions: {', '.join(extensions)}")
    
    if quick_mode:
        print(f"  Mode: Quick (using defaults)")
        
    print(f"  Subfolder handling: {subfolder_mode}")
    
    # Display optimization settings
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
    
    # Display upload settings
    print(f"  S3 Folder: {folder}")
    if folder_exists:
        print(f"  Include Existing Files: {'Yes' if include_existing else 'No'}")
    if rename_prefix:
        print(f"  Rename Prefix: {rename_prefix}")
        print(f"  Rename Mode: {rename_mode} (from config)")
    else:
        print("  No renaming")
    print(f"  Output Format: {selected_format.capitalize()} (from config)")
    print(f"  Concurrent Uploads: {concurrent} (from config)")
    
    # Check if user wants to cancel (non-quick mode only)
    if confirm.lower() != 'y':
        print("Upload cancelled.")
        return
    
    # =============== RUN OPTIMIZATION (DEFERRED UNTIL NOW) ===============
    
    # Initialize variables for the upload
    source_dir = '.'
    optimized_files = None
    
    # Now run the optimization if enabled
    if optimize and optimization_options:
        print("\nStarting media optimization...")
        # Pass the options to the optimizer
        source_dir, optimized_files = optimize_images('.', optimization_options)
        
        if not optimized_files:
            print("No files were optimized. Proceeding with regular upload.")
            source_dir = '.'
            optimized_files = None
        else:
            # Update the source directory to point to the optimized files
            print(f"Successfully optimized {len(optimized_files)} files in {source_dir}")
    
    # =============== RUN UPLOAD ===============
    
    # Run the upload with all settings
    upload_result = await upload_files(
        s3_folder=folder,
        extensions=extensions,
        rename_prefix=rename_prefix,
        rename_mode=rename_mode,
        only_first=only_first,
        max_concurrent=concurrent,
        source_dir=source_dir if source_dir == '.' else os.path.abspath(source_dir),  # Use absolute path if not current dir
        specific_files=optimized_files,
        include_existing=include_existing,
        output_format=selected_format,
        subfolder_mode=subfolder_mode
    )
    
    # Important: Change back to original directory if we changed it
    if source_dir != '.':
        os.chdir(original_dir)
        
    return upload_result

def run_cli():
    """
    Synchronous entry point for the CLI command.
    This function wraps the async main function with asyncio.run().
    """
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
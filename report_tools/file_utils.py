"""File utilities for finding and filtering document files."""

import os
import logging
from pathlib import Path
import config.config as config

def setup_logger(log_file=config.LOG_FILE):
    """Configure logging to file and console."""
    # Make sure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def get_ignored_directories(base_dir):
    """
    Get list of directories to ignore based on configuration.
    
    Args:
        base_dir: Base directory for resolving relative paths
        
    Returns:
        List of absolute directory paths to ignore
    """
    ignored_dirs = []
    
    # Use the STACKING_IGNORED_DIRECTORIES list from config
    for dir_name in config.STACKING_IGNORED_DIRECTORIES:
        abs_path = os.path.join(base_dir, dir_name)
        ignored_dirs.append(abs_path)
        print(f"Ignoring directory for stacking: {dir_name}")
    
    return ignored_dirs

def find_document_files(base_dir, recursive=config.RECURSIVE_SEARCH):
    """
    Find all supported document files in the directory (and subdirectories if recursive).
    
    Args:
        base_dir: Base directory to search
        recursive: Whether to search recursively
    
    Returns:
        List of Path objects for supported document files
    """
    base_path = Path(base_dir).resolve()
    
    # Get ignored directories for this run
    ignored_directories = [Path(d).resolve() for d in get_ignored_directories(base_dir)]
    
    document_files = []
    
    # Get list of enabled file extensions
    enabled_extensions = [ext for ext, enabled in config.FILE_TYPE_SUPPORT.items() 
                         if enabled]
    
    if not enabled_extensions:
        logging.warning("No file types are enabled in configuration. Check FILE_TYPE_SUPPORT settings.")
        return document_files
    
    logging.info(f"Searching for files with extensions: {', '.join(enabled_extensions)}")
    
    # Walk through directory structure
    if recursive:
        for root, dirs, files in os.walk(base_path):
            root_path = Path(root).resolve()
            
            # Skip ignored directories - compare path objects not strings
            should_skip = False
            for ignore_dir in ignored_directories:
                # Check if this directory is the ignored dir or is inside it
                if root_path == ignore_dir or root_path.is_relative_to(ignore_dir):
                    try:
                        # Print path relative to base directory
                        rel_path = root_path.relative_to(base_path)
                        print(f"Skipping ignored directory: {rel_path}")
                    except ValueError:
                        # Fallback if relative_to fails
                        print(f"Skipping ignored directory: {root_path.name}")
                    should_skip = True
                    break
            
            if should_skip:
                continue
                
            for file in files:
                file_path = Path(os.path.join(root, file))
                file_ext = file_path.suffix.lower()
                if file_ext in enabled_extensions:
                    document_files.append(file_path)
    else:
        # Non-recursive search - use glob for each extension
        for ext in enabled_extensions:
            document_files.extend(base_path.glob(f'*{ext}'))
    
    logging.info(f"Found {len(document_files)} document files")
    return document_files

# Keep the original function as an alias for backward compatibility
def find_markdown_files(base_dir, recursive=config.RECURSIVE_SEARCH):
    """
    Legacy function - alias for find_document_files.
    
    Args:
        base_dir: Base directory to search
        recursive: Whether to search recursively
    
    Returns:
        List of Path objects for document files
    """
    return find_document_files(base_dir, recursive)

def ensure_directory_exists(directory_path):
    """Create directory if it doesn't exist."""
    os.makedirs(directory_path, exist_ok=True)
    return directory_path  # Return the path after creating it
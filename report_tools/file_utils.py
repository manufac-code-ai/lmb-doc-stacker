"""File utilities for finding and filtering markdown reports."""

import os
import logging
from pathlib import Path
import config.config as config

def setup_logger(log_file=config.LOG_FILE):
    """Configure logging to file and console."""
    # Make sure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger()

def find_markdown_files(base_dir, recursive=config.RECURSIVE_SEARCH):
    """Find all markdown files in the directory (and subdirectories if recursive)."""
    base_path = Path(base_dir).resolve()  # Convert to absolute path
    all_files = []
    
    if recursive:
        # Recursive search with directory filtering
        for file_path in base_path.glob('**/*.md'):
            # Check if any ignored directory is in the path parts
            path_parts = file_path.parts
            should_ignore = False
            
            for ignored_dir in config.IGNORED_DIRECTORIES:
                if ignored_dir in path_parts:
                    # Silent ignore - don't log each file
                    should_ignore = True
                    break
            
            if not should_ignore:
                all_files.append(file_path)
    else:
        # Just find files in the top directory (no subdirectory filtering needed)
        all_files = list(base_path.glob('*.md'))
    
    logging.info(f"Found {len(all_files)} markdown files to process")
    return all_files

def get_ignored_reports():
    """Read the ignore file for reports that should be excluded from validation."""
    ignored_reports = set()
    
    if os.path.exists(config.IGNORE_FILE):
        with open(config.IGNORE_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                # Strip whitespace and skip empty lines or comments
                filename = line.strip()
                if filename and not filename.startswith('#'):
                    ignored_reports.add(filename)
                    
        if ignored_reports:
            logging.info(f"Found {len(ignored_reports)} reports to exclude from validation")
    
    return ignored_reports

def ensure_directory_exists(directory_path):
    """Ensure the specified directory exists."""
    os.makedirs(directory_path, exist_ok=True)
    return directory_path
"""
Configuration settings for document stacking.
This module centralizes all configurable parameters for the stacking process.
"""
from pathlib import Path

# Try to import local configuration (not tracked in git)
try:
    from config.config_loc import *
except ImportError:
    # Default fallback if no local config exists
    SOURCE_DIR = "_in"
    # Other defaults will be defined below

# If OUTPUT_DIR wasn't defined in local config, use default
if 'OUTPUT_DIR' not in locals():
    OUTPUT_DIR = "_out"       # Base output directory

RECURSIVE_SEARCH = True   # Whether to traverse subdirectories

# Output format configuration
OUTPUT_FORMAT = ".md"     # File extension for output files (options: ".md", ".txt")

# File type support configuration
FILE_TYPE_SUPPORT = {
    '.md': True,    # Markdown
    '.txt': False,   # Plain text
    '.docx': False, # Word documents (future implementation)
    '.pdf': False,  # PDF files (future implementation)
}

# Logging configuration
LOG_DIR = "_logs"  # Directory for log files
LOG_FILE = f"{LOG_DIR}/stack.log"  # Main stacking log

# ===== STACKING SPECIFIC SETTINGS =====
# Directories to exclude from stacking (if any)
STACKING_IGNORED_DIRECTORIES = []

# Stacking format settings
STACK_SEPARATOR = "\n\n------\n\n------\n\n"  # Separator between reports in stacks

# Human-readable titles configuration
TITLES_FOLDER = "__config"  # Relative path from SOURCE_DIR
TITLES_FILENAME = "readable_titles.csv"  # Filename within the __config folder

# ===== FILENAME SORTING CONFIGURATION =====
# Settings for extracting sort fields from filenames
FILENAME_PATTERNS = {
    # Regex for date extraction (currently YYMMDD)
    "date_pattern": r'(\d{6})(?:-\d+)?',
    
    # Position of date in filename (options: "prefix", "anywhere")
    "date_position": "prefix",
    
    # Default date string if none found - affects sort order
    "default_date": "000000",
    
    # Character(s) separating fields in filename
    "field_separator": " - ",
    
    # Fields to sort by, in priority order
    "sort_fields": ["date", "company", "room"],
    
    # Number of characters to skip after date before company field
    # Set to 0 if there's no consistent prefix length
    "date_field_gap": 1,
    
    # Whether to enable date-based sorting (False = alphabetical only)
    "use_date_sorting": True
}
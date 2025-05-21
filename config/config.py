"""
Configuration settings for document stacking.
This module centralizes all configurable parameters for the stacking process.
"""

# Source directory configuration
SOURCE_DIR = '"_in"'  # Default source directory
RECURSIVE_SEARCH = True   # Whether to traverse subdirectories

# Output configuration
OUTPUT_DIR = "_out"       # Base output directory
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
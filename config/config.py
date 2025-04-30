"""
Configuration settings for report validation.
This module centralizes all configurable parameters for the validation process.
"""

# Source directory configuration
SOURCE_DIR = '/Users/stevenbrown/Library/Mobile Documents/com~apple~CloudDocs/Documents_SRB iCloud/Projects/SOFTWARE dev SUPPORT projects/Ai MASTER CONTROL/Ai Projects per Model - Local/ChatGPT Projects - local storage/__cgpt_pj Job Dv Rpts/cgpt_pj Job Dv Rpts 9 REPORTS/svc rpts 1 basic'  # Default source directory
RECURSIVE_SEARCH = True   # Whether to traverse subdirectories

# Output configuration
OUTPUT_DIR = "_out"       # Base output directory
VALIDATED_DIR = "validated"  # Subdirectory for validation results

# Processing options
DEFAULT_REPORT_ONLY = True  # Default to report-only mode (no file moving)
STRICT_VALIDATION = False   # Default to normalized validation

# Display options
SHOW_VALID_REPORTS = False  # Whether to show valid reports in console output

# Directory exclusion settings
IGNORED_DIRECTORIES = [
    '_PM Reports',
    '_Diagnostic and Assist'
]

# File exclusion settings
IGNORE_FILE = "config/rep_ignore.txt"  # File containing list of reports to skip validation

# Log and analysis output configuration
LOG_DIR = "_logs"  # Directory for log files
LOG_FILE = f"{LOG_DIR}/val.log"  # Main validation log

# Analysis output files with clearer, shorter names
SUMMARY_LOG = f"{LOG_DIR}/val_summary.txt"  # Validation report summary
ERROR_SUMMARY = f"{LOG_DIR}/val_errors.csv"  # CSV of error frequencies
RARE_ERRORS = f"{LOG_DIR}/val_rare.txt"      # List of rare errors
WORD_COUNT_CSV = f"{LOG_DIR}/val_words.csv"  # Word count analysis
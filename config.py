"""
Configuration settings for report validation.
This module centralizes all configurable parameters for the validation process.
"""

# Source directory configuration
# SOURCE_DIR = "_md_input"  # Default source directory
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

# Log file path
LOG_FILE = "report_validation.log"
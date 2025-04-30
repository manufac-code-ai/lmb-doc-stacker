"""Core validation functionality for markdown service reports."""
# This file exists for backward compatibility

from report_tools.validation.core import normalize_markdown_content, validate_report
from report_tools.validation.processor import process_folder
from report_tools.validation.runner import run_validation

# Re-export functions to maintain backward compatibility
__all__ = ['normalize_markdown_content', 'validate_report', 
           'process_folder', 'run_validation']
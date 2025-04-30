"""Validation package for report structure checking."""

from report_tools.validation.core import normalize_markdown_content, validate_report
from report_tools.validation.processor import process_folder
from report_tools.validation.runner import run_validation

__all__ = ['normalize_markdown_content', 'validate_report', 
           'process_folder', 'run_validation']
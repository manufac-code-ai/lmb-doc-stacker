#!/usr/bin/env python3
"""Validate markdown service reports for proper structure."""

import argparse
import config.config as config
from report_tools.validation import run_validation

def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(description='Validate markdown service reports structure.')
    parser.add_argument('--input', default=config.SOURCE_DIR, 
                        help=f'Input folder containing markdown reports')
    parser.add_argument('--output', default=config.OUTPUT_DIR, 
                        help=f'Base output folder')
    parser.add_argument('--move', action='store_true', 
                        help='Move files instead of copying them')
    parser.add_argument('--strict', action='store_true', default=config.STRICT_VALIDATION,
                        help='Use strict validation without normalization')
    parser.add_argument('--report-only', action='store_true', default=config.DEFAULT_REPORT_ONLY,
                        help='Only analyze files without moving/copying')
    parser.add_argument('--no-recursive', action='store_true',
                        help='Do not search subdirectories for markdown files')
    parser.add_argument('--show-valid', action='store_true', 
                        help='Show valid reports in console output (default: hidden)')
    
    args = parser.parse_args()
    
    # Run the validation with the parsed arguments
    run_validation(args)

if __name__ == "__main__":
    main()

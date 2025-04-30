"""Batch processing of multiple report files."""

import os
import shutil
import logging
from pathlib import Path
from collections import Counter
import config.config as config
from report_tools import reporting
from report_tools.file_utils import find_markdown_files, get_ignored_reports
from report_tools.validation.core import validate_report

def process_folder(input_folder, output_base=config.OUTPUT_DIR, move_files=False, 
                  report_only=config.DEFAULT_REPORT_ONLY, strict=config.STRICT_VALIDATION,
                  show_valid=config.SHOW_VALID_REPORTS):
    """
    Process markdown files and sort them into categories.
    
    Args:
        input_folder: Path to folder containing markdown files
        output_base: Base folder name for output
        move_files: Whether to move files (True) or copy them (False)
        report_only: If True, don't move/copy files, just analyze
        strict: Use strict validation
        show_valid: Show valid reports in console output
        
    Returns:
        tuple: Stats for the processing run
    """
    # Find all markdown files, potentially in subdirectories
    markdown_files = find_markdown_files(input_folder)
    
    if not markdown_files:
        print(f"No markdown files found in {input_folder}{' or its subdirectories' if config.RECURSIVE_SEARCH else ''}")
        return 0, 0, 0, {}, {}
    
    # Create output directories with validated subdirectory
    validated_dir = Path(output_base) / config.VALIDATED_DIR
    valid_dir = validated_dir / "valid"
    invalid_dir = validated_dir / "invalid"
    
    valid_dir.mkdir(exist_ok=True, parents=True)
    invalid_dir.mkdir(exist_ok=True, parents=True)
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(config.SUMMARY_LOG), exist_ok=True)
    
    total_files = 0
    valid_files = 0
    invalid_files = 0
    ignored_files = 0
    error_counter = Counter()
    file_errors = {}
    
    # Get list of reports to ignore
    ignored_reports = get_ignored_reports()
    
    # Structures for tracking word counts
    word_counts = {
        "valid": [],
        "invalid": []
    }
    file_word_counts = {}
    
    with open(config.SUMMARY_LOG, 'w', encoding='utf-8') as log:
        log.write("Report Validation Summary\n")
        log.write("=======================\n\n")
        
        for file_path in markdown_files:
            total_files += 1
            
            # Check if this file should be ignored
            if file_path.name in ignored_reports:
                log.write(f"⚠️ IGNORED: {file_path.name} (explicitly excluded from validation)\n")
                logging.info(f"Skipping validation for ignored report: {file_path.name}")
                ignored_files += 1
                continue
            
            # Count words in the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                word_count = len(content.split())
                file_word_counts[file_path.name] = word_count
            
            # Validate the report
            is_valid, error_codes = validate_report(file_path, strict=strict)
            
            # Store the file's error codes for summary
            file_errors[file_path.name] = error_codes
            
            # Update error counter for CSV summary
            for error in error_codes:
                error_counter[error] += 1
            
            if is_valid:
                valid_files += 1
                word_counts["valid"].append(word_count)
                
                # Only move/copy if not in report-only mode
                if not report_only:
                    destination = valid_dir / file_path.name
                    if move_files:
                        shutil.move(str(file_path), str(destination))
                    else:
                        shutil.copy2(str(file_path), str(destination))
                
                # Still write to the log file but conditionally print to console
                log.write(f"✅ VALID: {file_path.name} ({word_count} words)\n")
                if show_valid:
                    logging.info(f"Valid report: {file_path.name}")
            else:
                invalid_files += 1
                word_counts["invalid"].append(word_count)
                
                # Only move/copy if not in report-only mode
                if not report_only:
                    destination = invalid_dir / file_path.name
                    if move_files:
                        shutil.move(str(file_path), str(destination))
                    else:
                        shutil.copy2(str(file_path), str(destination))
                
                log.write(f"❌ INVALID: {file_path.name} ({word_count} words)\n")
                log.write(f"  Errors: {', '.join(error_codes)}\n")
                # Use ERROR level for better visibility
                logging.error(f"INVALID: {file_path.name} - Errors: {error_codes}")
    
    # Calculate word count statistics
    word_stats = reporting.calculate_word_statistics(word_counts)
    
    # Generate reporting files
    reporting.write_summary_files(file_errors, file_word_counts, word_stats, error_counter)
    
    # Return statistics for display
    return valid_files, invalid_files, ignored_files, error_counter, word_stats
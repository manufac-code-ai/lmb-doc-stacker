import os
import shutil
import logging
import argparse
import csv
import re
import statistics  # Add this import for median calculation
from pathlib import Path
from datetime import datetime
from collections import Counter

# Import field definitions from the validation_fields module
from validation_fields import REQUIRED_FIELDS, FIELD_ALTERNATIVES, get_plain_field_name

def normalize_markdown_content(content):
    normalized = content
    
    # 1. First fix bold fields with colons/question marks outside the bold markers
    normalized = re.sub(r'\*\*(.*?)\*\*:', r'**\1:**', normalized)
    normalized = re.sub(r'\*\*(.*?)\*\*\?', r'**\1?**', normalized)
    
    # 2. Case-insensitive field normalization with exact patterns for problematic fields
    replacements = [
        # Next steps variations (both ? and : variants)
        (r'\*\*Next Steps\?\*\*', r'**Next steps?**'),
        (r'\*\*Next Steps:\*\*', r'**Next steps?**'),
        (r'\*\*Next steps:\*\*', r'**Next steps?**'),
        
        # Issue resolved variations 
        (r'\*\*Issue Resolved\?\*\*', r'**Issue resolved?**'),
        (r'\*\*Issue resolved:\*\*', r'**Issue resolved?**'),
        (r'\*\*Issues resolved:\*\*', r'**Issue resolved?**'),
        (r'\*\*Issues Resolved\?\*\*', r'**Issue resolved?**'),
        
        # Description problem/problems variations (with precise colon handling)
        (r'\*\*Description of problems:\*\*', r'**Description of problem:**'),
        (r'\*\*Description of Problems:\*\*', r'**Description of problem:**'),
        (r'\*\*Descriptions of problems:\*\*', r'**Description of problem:**'),
        (r'\*\*Descriptions of Problems:\*\*', r'**Description of problem:**'),
        
        # Description of work performed variations
        (r'\*\*Description of Work Performed:\*\*', r'**Description of work performed:**'),
        (r'\*\*Description of work Performed:\*\*', r'**Description of work performed:**'),
    ]
    
    # Apply each replacement
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    # 3. Replace alternative field names with canonical ones
    for canonical_field, alternatives in FIELD_ALTERNATIVES.items():
        for alt_field in alternatives:
            normalized = normalized.replace(alt_field, canonical_field)
    
    return normalized

def setup_logger(log_file='report_validation.log'):
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def validate_report(file_path):
    """
    Validate a markdown report file against the required structure.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        tuple: (is_valid, list_of_error_codes)
    """
    error_codes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            original_content = file.read()
            
            # Apply normalization preprocessing
            normalized_content = normalize_markdown_content(original_content)
            
            # First check if there are any fields at all (for UNSTRUCTURED_DOCUMENT)
            has_any_fields = False
            for field in REQUIRED_FIELDS:
                plain_field = field.replace('**', '')
                if plain_field in normalized_content:
                    has_any_fields = True
                    break
                
            if not has_any_fields:
                error_codes.append("UNSTRUCTURED_DOCUMENT")
                return False, error_codes
            
            # Check for presence of each required field
            for field in REQUIRED_FIELDS:
                plain_field = field.replace('**', '')
                
                if field not in normalized_content:
                    # Field is missing or not formatted correctly
                    if plain_field in normalized_content:
                        # Field exists but not bolded
                        field_name = get_plain_field_name(field)
                        error_codes.append(f"UNBOLDED_FIELD:{field_name}")
                    else:
                        # Field is completely missing (even after normalization)
                        field_name = get_plain_field_name(field)
                        error_codes.append(f"MISSING_FIELD:{field_name}")
            
            # Check for duplicated fields
            for field in REQUIRED_FIELDS:
                occurrences = normalized_content.count(field)
                if occurrences > 1:
                    field_name = get_plain_field_name(field)
                    error_codes.append(f"DUPLICATE_FIELD:{field_name}")
            
            # Check for empty fields (optional feature)
            for field in REQUIRED_FIELDS:
                if field in normalized_content:
                    field_pos = normalized_content.find(field) + len(field)
                    # Look for the next field or end of content
                    next_field_pos = float('inf')
                    for other_field in REQUIRED_FIELDS:
                        if other_field != field and other_field in normalized_content:
                            pos = normalized_content.find(other_field, field_pos)
                            if pos > field_pos and pos < next_field_pos:
                                next_field_pos = pos
                    
                    if next_field_pos == float('inf'):
                        next_field_pos = len(normalized_content)
                    
                    field_content = normalized_content[field_pos:next_field_pos].strip()
                    if not field_content:
                        field_name = get_plain_field_name(field)
                        error_codes.append(f"EMPTY_FIELD:{field_name}")
                    
        is_valid = len(error_codes) == 0
        return is_valid, error_codes
    
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return False, [f"ERROR:{str(e)}"]

def analyze_error_patterns(file_errors):
    """
    Create a reverse mapping of which files have each error type.
    
    Args:
        file_errors: Dictionary mapping filenames to their errors
        
    Returns:
        dict: Mapping from error codes to lists of filenames
    """
    error_to_files = {}
    
    for filename, errors in file_errors.items():
        for error in errors:
            if error not in error_to_files:
                error_to_files[error] = []
            error_to_files[error].append(filename)
    
    return error_to_files

def process_folder(input_folder, output_base="_md_output", move_files=False, report_only=False):
    """
    Process markdown files and sort them into categories.
    
    Args:
        input_folder: Path to folder containing markdown files
        output_base: Base folder name for output
        move_files: Whether to move files (True) or copy them (False)
        report_only: If True, don't move/copy files, just analyze
        
    Returns:
        tuple: (valid_count, invalid_count, pm_count, error_counter, word_stats)
    """
    input_path = Path(input_folder)
    
    # Create output directories
    valid_dir = Path(output_base) / "valid"
    invalid_dir = Path(output_base) / "invalid"
    pm_dir = Path(output_base) / "PM"  # New directory for PM reports
    
    valid_dir.mkdir(exist_ok=True, parents=True)
    invalid_dir.mkdir(exist_ok=True, parents=True)
    pm_dir.mkdir(exist_ok=True, parents=True)  # Create PM directory
    
    # Summary logs
    summary_log = Path(output_base) / "summary.txt"
    error_summary_csv = Path(output_base) / "error_summary.csv"
    rare_errors_log = Path(output_base) / "rare_errors.txt"
    word_count_csv = Path(output_base) / "word_counts.csv"  # New file for word count data
    
    total_files = 0
    valid_files = 0
    invalid_files = 0
    pm_files = 0  # Counter for PM files
    error_counter = Counter()
    file_errors = {}  # To store errors per file for the summary
    
    # New structures for tracking word counts
    word_counts = {
        "valid": [],
        "invalid": [],
        "pm": []
    }
    file_word_counts = {}  # To store word counts per file
    
    with open(summary_log, 'w', encoding='utf-8') as log:
        log.write("Report Validation Summary\n")
        log.write("=======================\n\n")
        
        for file_path in input_path.glob('*.md'):
            total_files += 1
            
            # Count words in the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                word_count = len(content.split())
                file_word_counts[file_path.name] = word_count
            
            # More robust PM detection
            pm_patterns = [
                r'[_\- ]pm', # Matches _pm, -pm, and space+pm
                r'pm[_\- ]',  # Matches pm_, pm-, and pm+space
                r'_PM',       # Explicit underscore+PM
                r'mentorpm'   # Special case for files like "MentorPM"
            ]
            
            is_pm_report = False
            for pattern in pm_patterns:
                if re.search(pattern, file_path.name, re.IGNORECASE):
                    is_pm_report = True
                    break
            
            if is_pm_report:
                # Handle PM reports - bypass validation and place in PM directory
                pm_files += 1
                word_counts["pm"].append(word_count)
                
                # Only move/copy if not in report-only mode
                if not report_only:
                    destination = pm_dir / file_path.name
                    if move_files:
                        shutil.move(file_path, destination)
                    else:
                        shutil.copy2(file_path, destination)
                
                log.write(f"🔧 PM REPORT: {file_path.name} ({word_count} words)\n")
                logging.info(f"PM report: {file_path.name}")
                continue  # Skip further processing
            
            # For non-PM reports, proceed with validation
            is_valid, error_codes = validate_report(file_path)
            
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
                        shutil.move(file_path, destination)
                    else:
                        shutil.copy2(file_path, destination)
                
                log.write(f"✓ VALID: {file_path.name} ({word_count} words)\n")
                logging.info(f"Valid report: {file_path.name}")
            else:
                invalid_files += 1
                word_counts["invalid"].append(word_count)
                
                # Only move/copy if not in report-only mode
                if not report_only:
                    destination = invalid_dir / file_path.name
                    if move_files:
                        shutil.move(file_path, destination)
                    else:
                        shutil.copy2(file_path, destination)
                
                log.write(f"✗ INVALID: {file_path.name} ({word_count} words)\n")
                log.write(f"  Errors: {', '.join(error_codes)}\n")
                logging.warning(f"{file_path.name}: {error_codes}")
        
        # Calculate word count statistics
        word_stats = {}
        for category, counts in word_counts.items():
            if counts:
                word_stats[category] = {
                    "average": sum(counts) / len(counts),
                    "median": statistics.median(counts) if counts else 0,
                    "min": min(counts) if counts else 0,
                    "max": max(counts) if counts else 0,
                    "total": sum(counts)
                }
            else:
                word_stats[category] = {"average": 0, "median": 0, "min": 0, "max": 0, "total": 0}
        
        # Write summary statistics with word counts
        log.write("\n\nSummary Statistics\n")
        log.write("==================\n")
        log.write(f"Total files processed: {total_files}\n")
        
        if total_files > 0:
            # Valid reports statistics
            log.write(f"Valid reports: {valid_files} ({valid_files/total_files*100:.1f}%)\n")
            if valid_files > 0:
                log.write(f"  Average length: {word_stats['valid']['average']:.1f} words\n")
                log.write(f"  Median length: {word_stats['valid']['median']} words\n")
                log.write(f"  Range: {word_stats['valid']['min']} to {word_stats['valid']['max']} words\n")
            
            # Invalid reports statistics
            log.write(f"Invalid reports: {invalid_files} ({invalid_files/total_files*100:.1f}%)\n")
            if invalid_files > 0:
                log.write(f"  Average length: {word_stats['invalid']['average']:.1f} words\n")
                log.write(f"  Median length: {word_stats['invalid']['median']} words\n")
                log.write(f"  Range: {word_stats['invalid']['min']} to {word_stats['invalid']['max']} words\n")
            
            # PM reports statistics
            log.write(f"PM reports: {pm_files} ({pm_files/total_files*100:.1f}%)\n")
            if pm_files > 0:
                log.write(f"  Average length: {word_stats['pm']['average']:.1f} words\n")
                log.write(f"  Median length: {word_stats['pm']['median']} words\n")
                log.write(f"  Range: {word_stats['pm']['min']} to {word_stats['pm']['max']} words\n")
        else:
            log.write("No files processed.\n")
    
    # Write word count CSV
    with open(word_count_csv, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["FILENAME", "WORD_COUNT", "CATEGORY"])
        
        # Add all files sorted by word count (descending)
        for filename, count in sorted(file_word_counts.items(), key=lambda x: x[1], reverse=True):
            category = "PM" if any(re.search(p, filename, re.IGNORECASE) for p in pm_patterns) else \
                       "Valid" if filename not in file_errors or not file_errors[filename] else "Invalid"
            csv_writer.writerow([filename, count, category])
    
    # Write error summary CSV
    with open(error_summary_csv, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["ERROR CODE", "COUNT"])
        for error, count in sorted(error_counter.items(), key=lambda x: x[1], reverse=True):
            csv_writer.writerow([error, count])
    
    # Analyze error patterns to identify rare errors and their files
    error_to_files = analyze_error_patterns(file_errors)
    
    # Write detailed report of rare errors (count <= 2)
    with open(rare_errors_log, 'w', encoding='utf-8') as rare_log:
        rare_log.write("Rare Error Analysis\n")
        rare_log.write("==================\n\n")
        rare_log.write("This report identifies files with uncommon errors (occurring in 2 or fewer files)\n\n")
        
        # Find rare errors
        rare_errors = {error: files for error, files in error_to_files.items() 
                      if len(files) <= 2}
        
        if rare_errors:
            for error, files in sorted(rare_errors.items()):
                rare_log.write(f"Error: {error}\n")
                rare_log.write("Files:\n")
                for file in files:
                    rare_log.write(f"  - {file}\n")
                rare_log.write("\n")
        else:
            rare_log.write("No rare errors found.\n")
    
    # Print rare errors to console for immediate attention
    if error_to_files:
        rare_errors = {error: files for error, files in error_to_files.items() 
                      if len(files) <= 2}
        if rare_errors:
            print("\nRare errors (occurring in 2 or fewer files):")
            for error, files in sorted(rare_errors.items()):
                print(f"  {error}: {', '.join(files)}")
            print(f"\nSee {output_base}/rare_errors.txt for complete details")
    
    logging.info(f"Processing complete. {valid_files} valid, {invalid_files} invalid, and {pm_files} PM reports identified.")
    
    if total_files == 0:
        print(f"No markdown files found in {input_folder}")
    
    return valid_files, invalid_files, pm_files, error_counter, word_stats

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Sort markdown reports based on structure validation.')
    parser.add_argument('--input', default='_md_input', help='Input folder containing markdown reports')
    parser.add_argument('--output', default='_md_output', help='Base output folder')
    parser.add_argument('--move', action='store_true', help='Move files instead of copying them')
    parser.add_argument('--log', default='report_validation.log', help='Log file path')
    parser.add_argument('--strict', action='store_true', help='Use strict validation without normalization')
    parser.add_argument('--report-only', action='store_true', help='Only analyze files without moving/copying')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger(args.log)
    
    # Make sure input folder exists
    if not os.path.exists(args.input):
        os.makedirs(args.input)
        print(f"Created input folder: {args.input}")
        print(f"Please place your markdown reports in this folder and run the script again.")
        return
    
    # Make sure output base folder exists
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    print(f"Starting report validation from {args.input}...")
    if args.strict:
        print("Using strict validation (no normalization)")
    else:
        print("Using normalized validation (accepting alternate field formats)")
    
    if args.report_only:
        print("Report-only mode: files will be analyzed but not moved/copied")
    
    valid, invalid, pm, error_counter, word_stats = process_folder(
        args.input, 
        args.output, 
        move_files=args.move,
        report_only=args.report_only
    )
    
    print(f"Processing complete! Valid: {valid}, Invalid: {invalid}, PM Reports: {pm}")
    
    # Print word count statistics
    if valid > 0:
        print(f"Valid reports average length: {word_stats['valid']['average']:.1f} words (range: {word_stats['valid']['min']} to {word_stats['valid']['max']} words)")
    if invalid > 0:
        print(f"Invalid reports average length: {word_stats['invalid']['average']:.1f} words (range: {word_stats['invalid']['min']} to {word_stats['invalid']['max']} words)")
    if pm > 0:
        print(f"PM reports average length: {word_stats['pm']['average']:.1f} words (range: {word_stats['pm']['min']} to {word_stats['pm']['max']} words)")
    
    if valid + invalid + pm > 0:
        print(f"See {args.output}/summary.txt for details")
        print(f"Word count analysis in {args.output}/word_counts.csv")
        print(f"Error frequency analysis in {args.output}/error_summary.csv")
        
        # Print top 5 most common errors
        if error_counter:
            print("\nTop issues found:")
            for error, count in sorted(error_counter.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {error}: {count} occurrences")

if __name__ == "__main__":
    main()

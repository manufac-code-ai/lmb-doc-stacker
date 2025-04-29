import os
import shutil
import logging
import argparse
import csv
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

# Import field definitions from the validation_fields module
from validation_fields import REQUIRED_FIELDS, FIELD_ALTERNATIVES, get_plain_field_name

def normalize_markdown_content(content):
    """
    Preprocess markdown content to normalize field labels and formatting.
    
    Args:
        content: The original markdown content
        
    Returns:
        str: normalized content
    """
    normalized = content
    
    # 1. Fix bold fields with colons/question marks outside the bold markers
    normalized = re.sub(r'\*\*(.*?)\*\*:', r'**\1:**', normalized)
    normalized = re.sub(r'\*\*(.*?)\*\*\?', r'**\1?**', normalized)
    
    # 2. Replace alternative field names with canonical ones
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

def process_folder(input_folder, output_base="_md_output", move_files=False):
    """
    Process markdown files and sort them into valid/invalid/unstructured categories.
    
    Args:
        input_folder: Path to folder containing markdown files
        output_base: Base folder name for output
        move_files: Whether to move files (True) or copy them (False)
    
    Returns:
        tuple: (valid_count, invalid_count, unstructured_count, error_counter)
    """
    input_path = Path(input_folder)
    
    # Create output directories
    valid_dir = Path(output_base) / "valid"
    invalid_dir = Path(output_base) / "invalid"
    unstructured_dir = Path(output_base) / "unstructured"  # New directory for unstructured docs
    
    valid_dir.mkdir(exist_ok=True, parents=True)
    invalid_dir.mkdir(exist_ok=True, parents=True)
    unstructured_dir.mkdir(exist_ok=True, parents=True)  # Create unstructured directory
    
    # Summary logs
    summary_log = Path(output_base) / "summary.txt"
    error_summary_csv = Path(output_base) / "error_summary.csv"
    rare_errors_log = Path(output_base) / "rare_errors.txt"
    
    total_files = 0
    valid_files = 0
    invalid_files = 0
    unstructured_files = 0  # Counter for unstructured files
    error_counter = Counter()
    file_errors = {}  # To store errors per file for the summary
    
    with open(summary_log, 'w', encoding='utf-8') as log:
        log.write("Report Validation Summary\n")
        log.write("=======================\n\n")
        
        for file_path in input_path.glob('*.md'):
            total_files += 1
            is_valid, error_codes = validate_report(file_path)
            
            # Store the file's error codes for summary
            file_errors[file_path.name] = error_codes
            
            # Update error counter for CSV summary
            for error in error_codes:
                error_counter[error] += 1
            
            if is_valid:
                valid_files += 1
                destination = valid_dir / file_path.name
                if move_files:
                    shutil.move(file_path, destination)
                else:
                    shutil.copy2(file_path, destination)
                log.write(f"✓ VALID: {file_path.name}\n")
                logging.info(f"Valid report: {file_path.name}")
            elif "UNSTRUCTURED_DOCUMENT" in error_codes:
                # Handle unstructured documents separately
                unstructured_files += 1
                destination = unstructured_dir / file_path.name
                if move_files:
                    shutil.move(file_path, destination)
                else:
                    shutil.copy2(file_path, destination)
                log.write(f"◯ UNSTRUCTURED: {file_path.name}\n")
                logging.info(f"Unstructured document: {file_path.name}")
            else:
                invalid_files += 1
                destination = invalid_dir / file_path.name
                if move_files:
                    shutil.move(file_path, destination)
                else:
                    shutil.copy2(file_path, destination)
                log.write(f"✗ INVALID: {file_path.name}\n")
                log.write(f"  Errors: {', '.join(error_codes)}\n")
                logging.warning(f"{file_path.name}: {error_codes}")
        
        # Write summary statistics
        log.write("\n\nSummary Statistics\n")
        log.write("==================\n")
        log.write(f"Total files processed: {total_files}\n")
        if total_files > 0:
            log.write(f"Valid reports: {valid_files} ({valid_files/total_files*100:.1f}%)\n")
            log.write(f"Invalid reports: {invalid_files} ({invalid_files/total_files*100:.1f}%)\n")
            log.write(f"Unstructured documents: {unstructured_files} ({unstructured_files/total_files*100:.1f}%)\n")
        else:
            log.write("No files processed.\n")
    
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
                      if len(files) <= 2 and error != "UNSTRUCTURED_DOCUMENT"}  # Exclude unstructured docs from rare errors
        
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
                      if len(files) <= 2 and error != "UNSTRUCTURED_DOCUMENT"}
        if rare_errors:
            print("\nRare errors (occurring in 2 or fewer files):")
            for error, files in sorted(rare_errors.items()):
                print(f"  {error}: {', '.join(files)}")
            print(f"\nSee {output_base}/rare_errors.txt for complete details")
    
    logging.info(f"Processing complete. {valid_files} valid, {invalid_files} invalid, and {unstructured_files} unstructured documents identified.")
    
    if total_files == 0:
        print(f"No markdown files found in {input_folder}")
    
    return valid_files, invalid_files, unstructured_files, error_counter

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Sort markdown reports based on structure validation.')
    parser.add_argument('--input', default='_md_input', help='Input folder containing markdown reports')
    parser.add_argument('--output', default='_md_output', help='Base output folder')
    parser.add_argument('--move', action='store_true', help='Move files instead of copying them')
    parser.add_argument('--log', default='report_validation.log', help='Log file path')
    parser.add_argument('--strict', action='store_true', help='Use strict validation without normalization')
    
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
        
    valid, invalid, unstructured, error_counter = process_folder(
        args.input, 
        args.output, 
        move_files=args.move
    )
    
    print(f"Processing complete! Valid: {valid}, Invalid: {invalid}, Unstructured: {unstructured}")
    if valid + invalid + unstructured > 0:
        print(f"See {args.output}/summary.txt for details")
        print(f"Error frequency analysis in {args.output}/error_summary.csv")
        
        # Print top 5 most common errors
        if error_counter:
            print("\nTop issues found:")
            for error, count in sorted(error_counter.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {error}: {count} occurrences")

if __name__ == "__main__":
    main()
